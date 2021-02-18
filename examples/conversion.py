from sentinel2download.downloader import Sentinel2Downloader
from sentinel2download.overlap import Sentinel2Overlap
from sentinel2preprocessing.conversion import Sentinel2Converter

if __name__ == '__main__':
    verbose = True
    aoi_path = "./test_geojson/osnova_lake.geojson"

    overlap = Sentinel2Overlap(aoi_path, verbose=verbose)
    tiles = overlap.overlap()

    print(f"Overlapped tiles: {tiles}")

    api_key = f"./.secret/sentinel2_google_api_key.json"

    loader = Sentinel2Downloader(api_key, verbose=verbose)

    product_type = 'L1C'
    start_date = "2018-05-01"
    end_date = "2018-05-05"
    download_dir = './sentinel2imagery/l1c_products'
    conversion_dir = './sentinel2imagery/l2a_products'
    cores = 3
    BANDS = {'TCI', 'B04', }
    CONSTRAINTS = {'NODATA_PIXEL_PERCENTAGE': 15.0, 'CLOUDY_PIXEL_PERCENTAGE': 10.0, }

    loaded = loader.download(product_type,
                             tiles,
                             start_date=start_date,
                             end_date=end_date,
                             output_dir=download_dir,
                             cores=cores,
                             bands=BANDS,
                             constraints=CONSTRAINTS,
                             full_download=True)

    converter = Sentinel2Converter(verbose=verbose)

    converted_products = converter.convert_all_products(download_dir, conversion_dir)
    print(f"Total number of converted products: {len(converted_products)}")

    print("Execution ended")
