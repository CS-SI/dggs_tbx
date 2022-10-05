import logging
import os
import shutil
from logging import INFO
from pathlib import Path
from tempfile import gettempdir

import geopandas as gpd
import h3pandas
import numpy as np
import rasterio.rio.mask
from rich.logging import RichHandler
from rich.progress import track
from shapely.geometry import box
from utils import db_connect

from dggs_tbx.utils import down_s2

FORMAT = "%(message)s"
logging.basicConfig(level=INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

logger = logging.getLogger(__name__)
logger.setLevel(INFO)


def h3_from_raster_extent(
    raster_path: Path, output_grid: Path, resolution: int,df_ret=False
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
        if df_ret:
            return gdf
        else:
            gdf.to_file(output_grid / out_fname, driver="GeoJSON")
            logger.info(f"-- Grid saved to: {output_grid/out_fname}")
            return output_grid / out_fname

def s2_to_h3(s2_tile_id: str,date="str", tmp_dir = Path(gettempdir()), res = 7, simulate=False):
    # Get all 10m tif files and store them in tmp dir
    # for each H3 cell load info from all bands
    # send dataframe to postgis

    # Download the Sentinel-2 data
    out_dir = down_s2(s2_tile_id,date,tmp_dir,bands=["B02","B08"])
    # Create a gdf of H3 hex at a given resolution
    list_bands = list(out_dir.rglob("*.tif"))
    h3_grid = h3_from_raster_extent(list_bands[0],out_dir,res,df_ret=True)
    if not simulate:
        # Fill the H3 dataframe
        band_values = {}
        for sat_band_path in track(list_bands):
            band_name = sat_band_path.parts[-1].replace(".tif","")
            band_values[band_name]=[]
            with rasterio.open(sat_band_path, "r") as src:
                shapes = [geom for geom in h3_grid.geometry]
                for shape in shapes:
                    try:
                        out_image, out_transform = rasterio.mask.mask(src, [shape],True)
                        sub_data = int(np.mean(out_image))
                        band_values[band_name].append(sub_data)
                    except:
                         logger.warning("Shape outside raster")
                         band_values[band_name].append(0)
        for band_val in band_values:
            h3_grid[band_val]=band_values[band_val]
    h3_grid["resolution"]=res
    # Add grid name
    h3_grid["grid_name"]="H3"

    # add column with the resolution
    h3_grid = h3_grid.to_crs("EPSG:4326")
    table_name="roma_h3"
    db = "start_db"
    engine = db_connect(db)
    h3_grid.to_postgis(table_name, engine, if_exists="append",index=True)
    shutil.rmtree(out_dir)
    logger.info(f" -- H3 data sent to {table_name} table ({len(h3_grid)} Cells)")

if __name__ == "__main__":
    import sys
    s2_to_h3("32TQM","20220902",res=int(sys.argv[1]), simulate=False)