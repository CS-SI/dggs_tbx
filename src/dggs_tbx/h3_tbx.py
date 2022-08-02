import logging
from logging import INFO
from pathlib import Path
import h3pandas
import geopandas as gpd
import rasterio.rio.mask
from rich.logging import RichHandler
from shapely.geometry import box

FORMAT = "%(message)s"
logging.basicConfig(level=INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

logger = logging.getLogger(__name__)
logger.setLevel(INFO)


def h3_from_raster_extent(
    raster_path: Path, output_grid: Path, resolution: int
) -> None:
    with rasterio.open(raster_path, "r") as ds:
        bounds = ds.bounds
        extent_geom = box(*bounds)
        df = gpd.GeoDataFrame({"id": 1, "geometry": [extent_geom]})
        df.crs = ds.crs
        df = df.to_crs("EPSG:4326")
        logger.info(f"H3 at resolution {resolution}")
        out_fname = f"{raster_path.stem}_H3_res_{resolution}_ap7.geojson"
        gdf = df.h3.polyfill_resample(resolution)
        gdf = gdf.to_crs(f"EPSG:{ds.crs.to_epsg()}")
        gdf.to_file(output_grid / out_fname, driver="GeoJSON")
        logger.info(f"-- Grid saved to: {output_grid/out_fname}")
    return output_grid / out_fname