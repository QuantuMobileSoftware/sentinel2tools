import configparser
import logging
import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from xml.dom import minidom
from xml.etree.ElementTree import ParseError

import pandas as pd

from sentinel2_download.code.settings import (BAND_RESOLUTIONS, PARENT_URL, STOP_SUFFIX,
                                              LEVEL_C_GCP_FOLDER, LEVEL_A_GCP_FOLDER,
                                              CONFIG_FILE, GLOBAL_TILE_DATE_INFOFILE,
                                              DOWNLOADED_IMAGES_DIR, MAX_WORKERS,
                                              MAXIMUM_EMPTY_PIXEL_PERCENTAGE, MAXIMUM_CLOUD_PERCENTAGE_ALLOWED)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('sentinel_download')


class SentinelDownload:
    _no_value_in_xml = 0.0

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)
        self.product_level = config['GCP']['LEVEL']
        self.channels = config['GCP']['BANDS'].split(' ')

        self.parent_url = PARENT_URL
        self.tiles_dates_list = pd.read_csv(GLOBAL_TILE_DATE_INFOFILE)
        self.tile_directories = {}
        if self.product_level == 'L2A':
            self.parent_url += LEVEL_A_GCP_FOLDER
        elif self.product_level == 'L1C':
            self.parent_url += LEVEL_C_GCP_FOLDER
        else:
            raise ValueError(f'Incorrect product level: {self.product_level}. '
                             'Required one of `L2A` or `L1C`.')

    def define_xml_node_value(self, xml_file_name, node):
        xml_dom = minidom.parse(xml_file_name)
        try:
            xml_node = xml_dom.getElementsByTagName(node)
            xml_node_value = xml_node[0].firstChild.data
            return xml_node_value
        except FileNotFoundError(f'No such file: {xml_file_name}'):
            logger.error('Error\n\n', exc_info=True)
            return self._no_value_in_xml
        except ParseError(f'no such node ({node}) in the {xml_file_name}'):
            logger.error('Error\n\n', exc_info=True)
            return self._no_value_in_xml

    def _check_quality(self, xml_file_name):
        self.gsutils_cp(xml_file_name, f'{DOWNLOADED_IMAGES_DIR}/MTD_TL.xml')
        xml_file_name = f'{DOWNLOADED_IMAGES_DIR}/MTD_TL.xml'
        nodata_pixel_value = float(self.define_xml_node_value(xml_file_name, 'NODATA_PIXEL_PERCENTAGE'))
        cloud_coverage_value = float(self.define_xml_node_value(xml_file_name, 'CLOUDY_PIXEL_PERCENTAGE'))

        if nodata_pixel_value >= MAXIMUM_EMPTY_PIXEL_PERCENTAGE:
            logger.info(f"Skipped: percent of empty pixels - {nodata_pixel_value} "
                        f"is higher than {MAXIMUM_EMPTY_PIXEL_PERCENTAGE} threshold from sentinel.config")
            return False
        if cloud_coverage_value >= MAXIMUM_CLOUD_PERCENTAGE_ALLOWED:
            logger.info(f"Skipped: percent of cloud coverage - {cloud_coverage_value} "
                        f"is higher than {MAXIMUM_CLOUD_PERCENTAGE_ALLOWED} threshold from sentinel.config")
            return False
        return True

    @staticmethod
    def _filter_folders(buckets):
        return [bucket for bucket in buckets if not bucket.endswith(STOP_SUFFIX)]

    def _get_files(self, url):
        buckets = subprocess.run(["gsutil", "ls", url],
                                 universal_newlines=True,
                                 stdout=subprocess.PIPE)
        buckets = buckets.stdout.splitlines()
        return self._filter_folders(buckets)

    def _retrieve_tile_info(self, tileID):
        if self.tile_directories.get(tileID) is None:
            url = f"{self.parent_url}/{tileID[:2]}/{tileID[2]}/{tileID[3:]}"
            self.tile_directories[tileID] = self._get_files(url)

    def _get_tile_path(self, tileID, img_date):
        self._retrieve_tile_info(tileID)
        for directory in self.tile_directories.get(tileID):
            if img_date in directory:
                return directory
        return None

    def _images_links(self, tileID, img_date, channels):
        link = self._get_tile_path(tileID, img_date)
        try:
            link += 'GRANULE'
            links = self._get_files(link)
        except TypeError:
            return {}

        if len(links) == 0 or len(links) > 1:
            return {}
        else:
            link = links[0]
            xml_metadata = link + 'MTD_TL.xml'
            if not self._check_quality(xml_metadata):
                return {}
            link += 'IMG_DATA/'
            image_links = {}
            for band in channels:
                if self.product_level == 'L2A' and band != 'CLD' and band != 'SLC':
                    resolution = BAND_RESOLUTIONS.get(band)
                    image_list = self._get_files(link + f'R{resolution}')
                if self.product_level == 'L1C' and band != 'CLD' and band != 'SLC':
                    image_list = self._get_files(link)
                if self.product_level == 'L2A' and band == 'CLD':
                    cloud_link = link.replace('IMG_DATA', 'QI_DATA')
                    image_list = [cloud_link + 'MSK_CLDPRB_20m.jp2']
                if self.product_level == 'L2A' and band == 'SCL':
                    resolution = BAND_RESOLUTIONS.get(band)
                    image_list = self._get_files(link + f'R{resolution}')
                image_links[band] = [image for image in image_list if band in image]
            return image_links

    @staticmethod
    def gsutils_cp(link, output_filename):
        subprocess.run(["gsutil", "cp", link, output_filename])

    def _retrieve_images(self, links, img_date, tileID):
        if len(links) > 0:
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                for band in links.keys():
                    if len(links[band]) == 1:
                        link = links[band][0]
                        save_path = f"{DOWNLOADED_IMAGES_DIR}/{self.product_level}_{tileID}_{img_date}"
                        os.makedirs(save_path, exist_ok=True)
                        output_filename = f"{save_path}/{self.product_level}_{tileID}_{img_date}_{band}.jp2"
                        if not os.path.exists(output_filename):
                            executor.submit(self.gsutils_cp, link, output_filename)
            return True
        return False

    def download(self):
        success_count = 0
        start_time = time.time()
        for idx, tile in self.tiles_dates_list.iterrows():
            tile_id = tile['tileID']
            img_date = str(tile['img_date'])
            logger.info(f"Tile number {idx} out of {len(self.tiles_dates_list)}, "
                        f"tile id - {tile_id}, "
                        f"image date - {img_date}")
            links = self._images_links(tile_id, img_date, self.channels)
            if self._retrieve_images(links, img_date, tile_id):
                success_count += 1
            # ! Uncomment this part if you are not sure in specified dates.
            # ! This will search images in GCP directory around specified date (+-2 days).
            else:
                for date_bias in range(-2, 3, 1):
                    img_date = int(img_date)
                    img_date_biased = str(int(img_date + date_bias))
                    links = self._images_links(tile_id, img_date_biased, self.channels)
                    if self._retrieve_images(links, img_date, tile_id):
                        success_count += 1
                        break
        end_time = time.time()
        logger.info(f'Downloaded: {success_count}/{len(self.tiles_dates_list)}')
        logger.info(f"Download took a total of {round((end_time - start_time) / 60, 2)} minutes")


if __name__ == '__main__':
    s2_download = SentinelDownload()
    s2_download.download()
