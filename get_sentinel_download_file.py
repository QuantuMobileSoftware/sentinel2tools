import argparse
from itertools import product
from typing import List
from datetime import datetime
import geopandas as gpd
import pandas as pd


def get_sentinel_tile_ids_by_aoi(aoi_poly_path: str, sentinel_tiles_path: str):
    aoi_poly_df = gpd.read_file(aoi_poly_path)
    sentinel_tiles_df = gpd.read_file(sentinel_tiles_path)
    tile_ids = get_intersection_tile_ids(aoi_poly_df, sentinel_tiles_df)
    return tile_ids


def get_intersection_tile_ids(aoi_poly_df: gpd.GeoDataFrame,
                              sentinel_polys_df: gpd.GeoDataFrame,
                              sentinel_tile_id_field: str = "Name") -> List[str]:
    intersection = gpd.overlay(aoi_poly_df, sentinel_polys_df, how='intersection')
    return intersection[sentinel_tile_id_field].drop_duplicates().tolist()


def generate_download_file(tile_ids: List[str],
                           save_path: str,
                           start_date: str,
                           end_date: str,
                           freq: str = 'D',
                           tile_id_field: str = 'tileID',
                           date_field: str = 'img_date') -> pd.DataFrame:
    dates: List[str] = (pd.date_range(start=start_date, end=end_date, freq=freq)
                        .format(formatter=lambda x: x.strftime('%Y%m%d')))

    tiles_ids_date_df = pd.DataFrame(list(product(tile_ids, dates)), columns=[tile_id_field, date_field])
    tiles_ids_date_df.to_csv(save_path, index=False)
    return tiles_ids_date_df


def parse_args():
    parser = argparse.ArgumentParser(
        description='Script for creating binary mask from geojson.')
    parser.add_argument(
        '-a', dest='aoi_poly_path',
        required=True, help='Path to the Area of Interest geojson file/shapefile with a polygon of AOI'
    )
    parser.add_argument(
        '-t', dest='sentinel_tiles_path',
        required=True, help='Path to the file with Sentinel-2 tile grid'
    )
    parser.add_argument(
        '-s', dest='save_path',
        required=True, help='Path where file for download with tile_id/date pairs will be saved'
    )
    parser.add_argument(
        '-sd', dest='start_date',
        required=False, default=datetime.today().strftime("%Y%m%d"),
        help='Date starting from which images should be downloaded'
    )
    parser.add_argument(
        '-ed', dest='end_date',
        required=False, default=datetime.today().strftime("%Y%m%d"),
        help='Date up until which images should be downloaded'
    )

    return parser.parse_args()


if __name__ == '__main__':
    args = parse_args()
    sentinel_tile_ids = get_sentinel_tile_ids_by_aoi(aoi_poly_path=args.aoi_poly_path,
                                                     sentinel_tiles_path=args.sentinel_tiles_path)
    generate_download_file(tile_ids=sentinel_tile_ids,
                           save_path=args.save_path,
                           start_date=args.start_date,
                           end_date=args.end_date)
