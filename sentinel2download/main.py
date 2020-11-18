from sentinel2download.downloader import Sentinel2Downloader


if __name__ == '__main__':
    api_key = f"../.secret/sentinel2_google_api_key.json"

    start_date = "2020-07-01"
    end_date = "2020-07-10"
    tiles = {'36UYB', }
    type_ = 'L1C'
    output_dir = '../sentinel2_imagery'
    cores = 1
    BANDS = {'TCI', 'B01', 'B02', 'B03', 'B04', 'B05', 'B06', 'B07', 'B08', 'B8A', 'B09', 'B10', 'B11', 'B12', }
    verbose = True

    CONSTRAINTS = {'NODATA_PIXEL_PERCENTAGE': 100.0, 'CLOUDY_PIXEL_PERCENTAGE': 100.0, }

    loader = Sentinel2Downloader(api_key)
    loaded = loader.download(type_, tiles, start_date=start_date, end_date=end_date, output_dir=output_dir, cores=2,
                             bands=BANDS, constraints=CONSTRAINTS, verbose=verbose)

    for l in loaded:
        print(l)
