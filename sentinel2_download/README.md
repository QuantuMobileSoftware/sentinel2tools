# SentinelDownload

The scripts to download Sentinel-2 images.


You need to specify TILE_ID and date for each image in `data/date_tile_info.csv` file.

To select the bands and product level to download, check the `code/sentinel.config` file (`BANDS` and `LEVEL` key). Quality contraints on the images could be specified in `code/settings.py` (`MAXIMUM_CLOUD_PERCENTAGE_ALLOWED` and `MAXIMUM_EMPTY_PIXEL_PERCENTAGE`).

Start downloading specified images via running the following command in `code/` directory:
```
python sentinel_download.py
```

This may require you to authorize in `gsutils`. To do so, simply follow the instructions after run.

Code is tested with `python3.8`, all packages are listed in `requirements.txt`

