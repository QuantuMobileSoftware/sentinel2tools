from sentinel2download.downloader import Sentinel2Downloader
from sentinel2download.overlap import Sentinel2Overlap

if __name__ == '__main__':
    verbose = True
    aoi_path = "../test_geojson/Kharkiv.geojson"

    overlap = Sentinel2Overlap(aoi_path, verbose=verbose)
    tiles = overlap.overlap()

    print(f"Overlapped tiles: {tiles}")

    api_key = f"../.secret/sentinel2_google_api_key.json"

    loader = Sentinel2Downloader(api_key, verbose=verbose)

    product_type = 'L1C'  # or L2A
    start_date = "2020-07-01"
    end_date = "2020-07-03"
    output_dir = '../sentinel2imagery'
    cores = 5
    BANDS = {'TCI', }
    CONSTRAINTS = {'NODATA_PIXEL_PERCENTAGE': 100.0, 'CLOUDY_PIXEL_PERCENTAGE': 100.0, }

    loaded = loader.download(product_type,
                             tiles,
                             start_date=start_date,
                             end_date=end_date,
                             output_dir=output_dir,
                             cores=cores,
                             bands=BANDS,
                             constraints=CONSTRAINTS)

    print(f"Load information")
    for item in loaded:
        print(item)

    print("Execution ended")
