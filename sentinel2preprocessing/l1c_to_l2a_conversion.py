import subprocess
import os
import logging
import time
from typing import List

logger = logging.getLogger(__name__)
logging.basicConfig()


class Sentinel2Converter:
    """
    Class for converting Sentinel2 L1C to L2A images
    """

    def __init__(self, verbose):
        """
        :param verbose: bool, flag, print logging information, default: False
        """
        if verbose:
            logger.setLevel(logging.INFO)
        else:
            logger.setLevel(logging.CRITICAL)

    def convert_l1c_to_l2a(self, input_tile_path, output_dir_path) -> bool:
        if not os.path.exists(input_tile_path):
            logger.error(f"Check that your input tile directory exists: {input_tile_path}")
            return False
        # Creating these folders is required for correct sen2cor processing
        os.makedirs(os.path.join(input_tile_path, "AUX_DATA"), exist_ok=True)
        os.makedirs(os.path.join(input_tile_path, "HTML"), exist_ok=True)
        logger.info(f"Started converting {input_tile_path}")
        process = subprocess.run(['L2A_Process', f'--output_dir={output_dir_path}', f'{input_tile_path}'],
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 universal_newlines=True)
        success = process.returncode == 0
        if success:
            logger.info(f"Successfully processed {input_tile_path}, results are stored at {output_dir_path}")
        else:
            logger.error(f"Something went wrong when trying to convert L1C product {input_tile_path} "
                         f"to L2A product: {process.stderr}")
        return success

    def convert_all_products(self, input_dir_path, output_dir_path) -> List[str]:
        """
        :param input_dir_path: str, path to a directory with downloaded Sentinel-2 L1C products
        :param output_dir_path: list, tiles to load (ex: {36UYA, 36UYB})
        :return: List[str],
        """
        start_time = time.time()
        logger.info(f"Started converting L1C products into L2A products")
        if not os.path.exists(input_dir_path):
            logger.info(f"Check that your input directory exists: {input_dir_path}")
        os.makedirs(output_dir_path, exist_ok=True)
        results = []
        for input_tile in os.listdir(input_dir_path):
            input_tile_path = os.path.join(input_dir_path, input_tile)
            status = self.convert_l1c_to_l2a(input_tile_path, output_dir_path)
            if status:
                results.append(input_tile_path)
        logger.info(f"Finished converting at {time.strftime('%H:%M:%S', time.gmtime(time.time() - start_time))}")
        return results
