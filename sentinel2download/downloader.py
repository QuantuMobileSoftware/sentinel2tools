import os
import re
import logging
import time

from datetime import datetime, timedelta
from collections import namedtuple
from types import MappingProxyType
from typing import Optional, List
from xml.dom import minidom
from google.cloud import storage
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

PRODUCT_TYPE = namedtuple('type', 'L2A L1C')('L2A', 'L1C')

BANDS = frozenset(('TCI', 'B01', 'B02', 'B03', 'B04', 'B05', 'B06',
                   'B07', 'B08', 'B8A', 'B09', 'B10', 'B11', 'B12',))

CONSTRAINTS = MappingProxyType({'CLOUDY_PIXEL_PERCENTAGE': 100.0, })


class Sentinel2Downloader:
    """
    Class for loading Sentinel2 L1C or L2A images
    """

    def __init__(self, api_key: str, verbose: bool = False):
        """
        :param api_key: str, path to google key, https://cloud.google.com/storage/docs/public-datasets/sentinel-2
        :param verbose: bool, flag, print logging information, default: False
        """
        if verbose:
            logging.basicConfig(level=logging.INFO)

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = api_key
        self.client = storage.Client()
        self.bucket = self.client.get_bucket('gcp-public-data-sentinel-2')
        self.metadata_suffix = 'MTD_TL.xml'

    def _filter_by_dates(self, safe_prefixes):
        # acquired date: 20200812T113607
        date_pattern = r"_(\d+)T\d+_"
        filtered = list()
        for safe_prefix in safe_prefixes:
            search = re.search(date_pattern, safe_prefix)
            date = search.group(1)
            date = datetime.strptime(date, '%Y%m%d')
            if date in self.date_range:
                filtered.append(safe_prefix)
        return filtered

    def _tile_prefix(self, tile):
        prefix = f"tiles/{tile[:2]}/{tile[2]}/{tile[3:]}/"
        if self.product_type == PRODUCT_TYPE.L2A:
            prefix = "L2/" + prefix
        return prefix

    @staticmethod
    def _date_range(start_date, end_date):
        days = (end_date - start_date).days
        date_range = [start_date + timedelta(days=delta) for delta in range(0, days + 1)]
        return date_range

    def _get_safe_prefixes(self, prefix, delimiter='/'):
        iterator = self.client.list_blobs(self.bucket, prefix=prefix, delimiter=delimiter)
        prefixes = set()
        for page in iterator.pages:
            prefixes.update(page.prefixes)
        return prefixes

    def _file_suffixes(self):
        if self.product_type == 'L2A':
            file_suffixes = list()
            for band in self.bands:
                if band in ('TCI', 'B02', 'B03', 'B04', 'B08'):
                    suffix = f"{band}_10m.jp2"
                elif band in ('B05', 'B06', 'B07', 'B8A', 'B11', 'B12'):
                    suffix = f"{band}_20m.jp2"
                else:
                    suffix = f"{band}_60m.jp2"
                file_suffixes.append(suffix)
        else:
            file_suffixes = [f"{band}.jp2" for band in self.bands]
        return file_suffixes

    def _match_constraints(self, metadata_blob):
        try:
            metadata = metadata_blob.download_as_string()
            xml_dom = minidom.parseString(metadata)

            for constraint, value in self.constraints.items():
                xml_node = xml_dom.getElementsByTagName(constraint)
                if xml_node:
                    parsed_value = float(xml_node[0].firstChild.data)
                    if parsed_value > value:
                        return False
                else:
                    logger.info(f"Constraint: {constraint} not present in metadata: {metadata_blob.name}")
        except Exception as ex:
            logger.info(f"Error parsing blob metadata: {metadata_blob.name}: {str(ex)}")
            return False
        else:
            return True

    def get_save_path(self, blob):
        name = blob.name
        # extract dirname, for ex: S2A_MSIL2A_20200703T084601_N0214_R107_T36UYA_20200703T113817
        search = re.search(r"/([^/]+)\.SAFE", name)
        save_dir = search.group(1)
        save_path = Path(self.output_dir) / Path(save_dir) / Path(name).name

        if save_path.is_file():
            logger.info(f"Blob {save_path} exists!")
            return
        else:
            return save_path

    def _filter_by_suffix(self, blobs, file_suffixes):
        blobs_to_load = set()
        for blob in blobs:
            if blob.name.endswith(self.metadata_suffix):
                if not self._match_constraints(blob):
                    return
                else:
                    blobs_to_load.add(blob)
            for suffix in file_suffixes:
                if blob.name.endswith(suffix):
                    blobs_to_load.add(blob)
        return blobs_to_load

    def blobs_to_load(self, tile_prefix):
        blobs_to_load = set()
        file_suffixes = self._file_suffixes()
        # filter store items by base prefix, ex: tiles/36/U/YA/
        safe_prefixes = self._get_safe_prefixes(tile_prefix)
        print("SAFE")
        print(len(safe_prefixes))
        # filter .SAFE paths by date range
        filtered_prefixes = self._filter_by_dates(safe_prefixes)
        for prefix in filtered_prefixes:
            granule_prefix = prefix + "GRANULE/"
            blobs = list(self.client.list_blobs(self.bucket, prefix=granule_prefix))

            granule_blobs = self._filter_by_suffix(blobs, file_suffixes)
            if granule_blobs:
                blobs_to_load.update(granule_blobs)

        return blobs_to_load

    def download_blob(self, blob):
        save_path = self.get_save_path(blob)
        # check if file exists
        if not save_path:
            return False, blob.name
        Path.mkdir(save_path.parent, parents=True, exist_ok=True)

        with open(save_path, 'wb') as file:
            blob.download_to_file(file)
        logger.info(f"Loaded {blob.name}")
        return True, blob.name

    def download_blobs_mult(self, blobs):
        results = list()
        with ThreadPoolExecutor(max_workers=self.cores) as executor:
            future_to_blob = {executor.submit(self.download_blob, blob): blob.name for blob in blobs}
            for future in as_completed(future_to_blob):
                blob_name = future_to_blob[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as ex:
                    logger.info(f"Error while loading {blob_name}: {str(ex)}")
                    results.append((False, blob_name))
        return results

    def _setup(self, product_type, tiles, start_date, end_date, bands,
               constraints, output_dir, cores):
        if product_type not in PRODUCT_TYPE:
            raise ValueError(f"Provide proper Sentinel2 type: {PRODUCT_TYPE}")
        self.product_type = product_type

        self.tiles = tiles

        format = '%Y-%m-%d'
        if end_date:
            end_date = datetime.strptime(end_date, format)
        else:
            now = datetime.now()
            end_date = datetime(now.year, now.month, now.day)
        if start_date:
            start_date = datetime.strptime(start_date, format)
        else:
            delta = 2
            start_date = end_date - timedelta(days=delta)

        self.date_range = self._date_range(start_date, end_date)

        bands = set(bands).intersection(BANDS)
        if not bands:
            raise ValueError(f"Provide bands from available set: {BANDS}")
        else:
            self.bands = bands

        self.constraints = constraints
        self.output_dir = output_dir
        self.cores = cores

    def download(self,
                 product_type,
                 tiles: list,
                 *,
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 bands: set = BANDS,
                 constraints: dict = CONSTRAINTS,
                 output_dir: str = '../sentinel2imagery',
                 cores: int = 5) -> Optional[List]:
        """
        :param product_type: str, "L2A" or "L1C" Sentinel2 products
        :param tiles: list, tiles to load (ex: {36UYA, 36UYB})
        :param start_date: str, format: 2020-01-01, start date to search and load blobs, default: (today - 2 days)
        :param end_date:  str, format: 2020-01-02, end date to search and load blobs, default: today
        :param bands: set, selected bands for loading, default: {'TCI', 'B01', 'B02', 'B03', 'B04', 'B05', 'B06',
                                                                'B07', 'B08', 'B8A', 'B09', 'B10', 'B11', 'B12', }
        :param constraints: dict, constraints that blobs must match, default: TODO: SPECIFY
        :param output_dir: str, path to loading dir, default: '../sentinel2imagery'
        :param cores: int, number of cores, default: 5
        :return: [tuple, None], tuples (flag, blob_name), if flag=True, blob is loaded, or None if nothing to load
        """

        self._setup(product_type, tiles, start_date, end_date, bands, constraints, output_dir, cores)

        logger.info("Start downloading...")
        start_time = time.time()
        results = list()
        for tile in tiles:
            logger.info(f"Loading blobs for tile {tile}...")

            tile_prefix = self._tile_prefix(tile)
            blobs_to_load = self.blobs_to_load(tile_prefix)
            result = self.download_blobs_mult(blobs_to_load)
            results.extend(result)

            logger.info(f"Finished loading blobs for tile {tile}")

        logger.info(f"Loaded: {len([r[0] for r in results if r[0]])} blobs")
        logger.info(f"\nFinished loading at {time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time))}")

        return results
