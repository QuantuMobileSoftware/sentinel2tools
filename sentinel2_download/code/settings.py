import os


def path_exists_or_create(path):
    if not os.path.exists(path):
        os.makedirs(path)
    return path


DATA_PATH = '../data'

BAND_RESOLUTIONS = {'TCI': '10m',
                    'B01': '60m',
                    'B02': '10m',
                    'B03': '10m',
                    'B04': '10m',
                    'B05': '20m',
                    'B06': '20m',
                    'B07': '20m',
                    'B08': '10m',
                    'B8A': '20m',
                    'B09': '60m',
                    'B10': '60m',
                    'B11': '20m',
                    'B12': '20m',
                    'SCL': '20m'}
PARENT_URL = 'gs://gcp-public-data-sentinel-2'
STOP_SUFFIX = '_$folder$'
LEVEL_C_GCP_FOLDER = '/tiles'
LEVEL_A_GCP_FOLDER = '/L2/tiles'
CONFIG_FILE = 'sentinel.config'
GLOBAL_TILE_DATE_INFOFILE = f'{DATA_PATH}/date_tile_info.csv'
DOWNLOADED_IMAGES_DIR = path_exists_or_create(f'{DATA_PATH}/input')
MAX_WORKERS = 8
MAXIMUM_CLOUD_PERCENTAGE_ALLOWED = 40.0
MAXIMUM_EMPTY_PIXEL_PERCENTAGE = 15.0
