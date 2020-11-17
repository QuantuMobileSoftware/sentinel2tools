import os
import re

from datetime import datetime, timedelta
from collections import namedtuple
from xml.dom import minidom
from google.cloud import storage
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

PRODUCT_TYPE = namedtuple('type', 'L2A L1C')('L2A', 'L1C')

BANDS = ['TCI', 'B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B09', 'B10', 'B11', 'B12', ]

CONSTRAINTS = {'NODATA_PIXEL_PERCENTAGE': 100.0, 'CLOUDY_PIXEL_PERCENTAGE': 100.0, }


class Sentinel2Downloader:
    def __init__(self):
        user = os.getenv('NB_USER')
        # os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f"/home/{user}/work/key.json"
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f"../.secure/key.json"

        self.client = storage.Client()
        self.bucket = self.client.get_bucket('gcp-public-data-sentinel-2')

        self.metadata_suffix = 'MTD_TL.xml'

    def _filter_by_dates(self, safe_prefixes, date_range):
        # acquired date: 20200812T113607
        date_pattern = r"_(\d+)T\d+_"
        filtered = list()
        for safe_prefix in safe_prefixes:
            search = re.search(date_pattern, safe_prefix)
            date = search.group(1)
            date = datetime.strptime(date, '%Y%m%d')
            if date in date_range:
                filtered.append(safe_prefix)
        return filtered

    def _tile_prefix(self, type, tile):
        prefix = f"tiles/{tile[:2]}/{tile[2]}/{tile[3:]}/"
        if type == PRODUCT_TYPE.L2A:
            prefix = "L2/" + prefix
        return prefix

    def _date_range(self, start_date, end_date, format='%Y-%m-%d'):
        start_date = datetime.strptime(start_date, format)
        end_date = datetime.strptime(end_date, format)

        days = (end_date - start_date).days
        date_range = [start_date + timedelta(days=delta) for delta in range(0, days + 1)]

        return date_range

    def _get_prefixes(self, prefix, delimiter='/'):
        iterator = self.client.list_blobs(self.bucket, prefix=prefix, delimiter=delimiter)
        prefixes = set()
        for page in iterator.pages:
            prefixes.update(page.prefixes)
        return prefixes

    def _file_suffixes(self, type, bands):
        if type == 'L2A':
            file_suffixes = list()
            for band in bands:
                if band in ('TCI', 'B02', 'B03', 'B04', 'B08'):
                    suffix = f"{band}_10m.jp2"
                elif band in ('B05', 'B06', 'B07', 'B8A', 'B11', 'B12'):
                    suffix = f"{band}_20m.jp2"
                else:
                    suffix = f"{band}_60m.jp2"
                file_suffixes.append(suffix)
        else:
            file_suffixes = [f"{band}.jp2" for band in bands]

        print("FILE SUFFEXES")
        print(file_suffixes)
        return file_suffixes

    def _match_constraints(self, metadata_blob):
        try:
            metadata = metadata_blob.download_as_string()
            xml_dom = minidom.parseString(metadata)

            for constraint, value in CONSTRAINTS.items():
                xml_node = xml_dom.getElementsByTagName(constraint)
                if xml_node:
                    parsed_value = float(xml_node[0].firstChild.data)
                    if parsed_value > value:
                        return False
                else:
                    print(f"Constraint: {constraint} not present in metadata: {metadata_blob.name}")
        except Exception as ex:
            print(f'Error parsing metadata: {str(ex)}')
            return False
        else:
            return True

    def get_save_path(self, blob, output_dir):
        name = blob.name
        # extract dirname, for ex: S2A_MSIL2A_20200703T084601_N0214_R107_T36UYA_20200703T113817
        search = re.search(r"/([^/]+)\.SAFE", name)
        save_dir = search.group(1)
        save_path = Path(output_dir) / Path(save_dir) / Path(name).name

        print("SAVEPATH")
        print(save_path)
        if save_path.is_file():
            print(f"ASSET EXISTS: {save_path}")
            return
        else:
            return save_path

    def get_links_to_load(self, blobs, file_suffixes):
        assets = set()
        for blob in blobs:
            if blob.name.endswith(self.metadata_suffix):
                if not self._match_constraints(blob):
                    return
                else:
                    assets.add(blob)
            for suffix in file_suffixes:
                if blob.name.endswith(suffix):
                    assets.add(blob)
        return assets

    def get_to_load(self, tile_prefix, type, date_range):
        to_load = set()
        file_suffixes = self._file_suffixes(type, BANDS)
        # filter store items by base prefix, ex: tiles/36/U/YA/
        safe_prefixes = self._get_prefixes(tile_prefix)
        print("SAFE")
        print(len(safe_prefixes))
        # filter .SAFE paths by date range
        filtered_prefixes = self._filter_by_dates(safe_prefixes, date_range)

        print("FILTERED PREFIXES")
        print(filtered_prefixes)
        for prefix in filtered_prefixes:
            granule_prefix = prefix + "GRANULE/"
            blobs = list(self.client.list_blobs(self.bucket, prefix=granule_prefix))

            links = self.get_links_to_load(blobs, file_suffixes)
            if links:
                to_load.update(links)

        return to_load

    def download_assets(self, asset, output_dir):
            save_path = self.get_save_path(asset, output_dir)
            # check if file exists
            if not save_path:
                return
            Path.mkdir(save_path.parent, parents=True, exist_ok=True)
            print(f"Loading to {save_path}")

            with open(save_path, 'wb') as file:
                asset.download_to_file(file)

    def load_assets(self, assets_list, output_dir, cores):
        with ThreadPoolExecutor(max_workers=cores) as executor:
            futures = [executor.submit(self.download_assets, asset, output_dir) for asset in assets_list]
            for future in as_completed(futures):
                try:
                    data = future.result()
                    print("DATA")
                    print(data)
                except Exception as ex:
                    print(f"Error while loading: {str(ex)}")

    def download(self, type, tiles, start_date, end_date, output_dir, cores):

        for tile in tiles:
            print(f"Loading assets for tile {tile}")

            date_range = self._date_range(start_date, end_date)
            tile_prefix = self._tile_prefix(type, tile)
            print("TILE PREFIX")
            print(tile_prefix)
            to_load = self.get_to_load(tile_prefix, type, date_range)

            print("TO LOAD")
            print(len(to_load))
            for load in to_load:
                print(load)

            self.load_assets(to_load, output_dir, cores)
