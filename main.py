from sentinel2download.downloader import Sentinel2Downloader
from sentinel2download.overlap import Sentinel2Overlap

if __name__ == '__main__':
    api_key = f"../.secret/sentinel2_google_api_key.json"

    start_date = "2020-07-01"
    end_date = "2020-07-10"
    tiles = ['36UYB', ]
    type_ = 'L1C'  # or L2A
    output_dir = '../sentinel2imagery'
    cores = 5
    BANDS = frozenset(('TCI', 'B01', 'B02', 'B03', 'B04', 'B05', 'B06',
                       'B07', 'B08', 'B8A', 'B09', 'B10', 'B11', 'B12',))

    BANDS = {'TCI', }
    verbose = True
    CONSTRAINTS = {'NODATA_PIXEL_PERCENTAGE': 100.0, 'CLOUDY_PIXEL_PERCENTAGE': 100.0, }

    aoi_path = "./input/Kharkiv_region.geojson"
    # aoi_path = "./input/ohio_AOI.geojson"
    # grid_path = "grid/sentinel2grid.shp"

    overlap = Sentinel2Overlap(aoi_path, verbose=True)
    tiles = overlap.overlap()
    print(tiles)
    # for testing, not too long loading
    tiles = tiles[:3]

    loader = Sentinel2Downloader(api_key, verbose=True)
    loaded = loader.download(type_, tiles,
                             start_date=start_date,
                             end_date=end_date,
                             output_dir=output_dir,
                             cores=cores,
                             bands=BANDS, constraints=CONSTRAINTS)

    for l in loaded:
        print(l)
