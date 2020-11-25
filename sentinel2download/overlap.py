import os
import os.path
import geopandas as gp
import logging
from shapely.geometry import box
from typing import Optional, List

logger = logging.getLogger(__name__)

GRID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "./grid"))


class Sentinel2Overlap:
    def __init__(self, aoi_path: str, *, grid_path: str = os.path.join(GRID_DIR, "sentinel2grid.shp"), verbose: bool = False):
        self.crs = "epsg:4326"

        if verbose:
            logging.basicConfig(level=logging.INFO)
        aoi = gp.read_file(aoi_path)

        if len(aoi) > 1 or aoi.geometry[0].geom_type != 'Polygon':
            logger.info(f"Input file contains more than 1 features or feature is not Polygon."
                        f"Bound box will be created.")
            bbox = box(*aoi.total_bounds)
            logger.info(f"Bound box: {bbox}")
            aoi = gp.GeoDataFrame(geometry=[bbox], crs=self.crs)

        self.aoi = aoi
        self.grid = gp.read_file(grid_path)

    def _intersect(self, limit):
        """
        Find all tiles that intersects given region with area >= limit km2
        :param limit: float, min intersection area in km2
        :return: (GeoDataFrame, epsg), precised intersected tiles and UTM zone code
        """

        # Get the indices of the tiles that are likely to be inside the bounding box of the given Polygon
        aoi = self.aoi
        grid = self.grid
        geometry = aoi.geometry[0]

        tiles_indexes = list(grid.sindex.intersection(geometry.bounds))
        grid = grid.loc[tiles_indexes]
        # Make the precise tiles in Polygon query

        grid = grid.loc[grid.intersects(geometry)]

        # intersection area
        epsg = self.epsg_code(geometry.centroid.x, geometry.centroid.y)

        # to UTM projection in meters
        aoi['geometry'] = aoi.geometry.to_crs(epsg=epsg)
        grid['geometry'] = grid.geometry.to_crs(epsg=epsg)

        grid['area'] = grid.geometry.apply(lambda g: g.intersection(aoi.geometry[0]).area / 1e6)
        grid = grid.loc[grid['area'] >= limit]
        grid = grid.sort_values(by=['area', 'Name'], ascending=[False, True])

        return grid, epsg

    def overlap(self, *, limit: float = 0.001) -> Optional[List]:
        """
        Find unique tiles that intersects given aoi, area
        :param limit: float, min intersection area in km2
        :return: list, list of tiles
        """

        logger.info(f"Start finding overlapping tiles")

        grid, epsg = self._intersect(limit)

        aoi = self.aoi
        overlap_tiles = list()
        for row in grid.itertuples():
            start_area = aoi.geometry[0].area
            aoi.geometry[0] = aoi.geometry[0].difference(row.geometry)
            if start_area != aoi.geometry[0].area:
                overlap_tiles.append(dict(Name=row.Name, geometry=row.geometry))

        if not overlap_tiles:
            return

        tiles = gp.GeoDataFrame(overlap_tiles, crs=epsg)
        tiles = tiles.to_crs(self.crs)

        tile_names = sorted(tiles.Name)
        logger.info(f"Found {len(tile_names)} tiles: {', '.join(tile_names)}")
        return tile_names

    @staticmethod
    def epsg_code(longitude, latitude):
        """
        Generates EPSG code from lon, lat
        :param longitude: float
        :param latitude: float
        :return: int, EPSG code
        """

        def _zone_number(lat, lon):
            if 56 <= lat < 64 and 3 <= lon < 12:
                return 32
            if 72 <= lat <= 84 and lon >= 0:
                if lon < 9:
                    return 31
                elif lon < 21:
                    return 33
                elif lon < 33:
                    return 35
                elif lon < 42:
                    return 37

            return int((lon + 180) / 6) + 1

        zone = _zone_number(latitude, longitude)

        if latitude > 0:
            return 32600 + zone
        else:
            return 32700 + zone
