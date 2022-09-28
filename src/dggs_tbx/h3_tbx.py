import logging
import os
import shutil
from logging import INFO
from pathlib import Path
from tempfile import gettempdir

import boto3
import geopandas as gpd
import h3pandas
import numpy as np
import rasterio.rio.mask
from botocore import UNSIGNED
from botocore.config import Config
from rich.logging import RichHandler
from rich.progress import track
from shapely.geometry import box
from sqlalchemy import create_engine

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
    if date[5]==0:
        month = date[6]
    else:
        month = date[5:6]
    prefix = f"sentinel-s2-l2a-cogs/{s2_tile_id[:2]}/{s2_tile_id[2:3]}/{s2_tile_id[3:]}/{date[:4]}/{month}/"
    client = boto3.client('s3', config=Config(signature_version=UNSIGNED))
    bucket_name = "sentinel-cogs"
    default_kwargs = {
        "Bucket": bucket_name ,
        "Prefix": prefix,
    }
    response = client.list_objects_v2(**default_kwargs)
    contents = response.get("Contents")
    logger.info(" -- S3 response recieved")
    bands=["B02","B08"]
    for resp in contents:
        key = resp["Key"]
        band = key.split("/")[-1].replace(".tif","")
        if date in resp["Key"] and band in bands:
            product_name = key.split("/")[-2]
            out_dir = tmp_dir/product_name
            out_dir.mkdir(parents=True,exist_ok=True)
            file_name = out_dir/Path(band+".tif")
            client.download_file(
                bucket_name,
                resp["Key"],
                str(file_name)
            )
            logger.info(f" -- Saved {band} to {file_name}")
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
    h3_grid["H3_resolution"]=res
    # add column with the resolution
    h3_grid = h3_grid.to_crs("EPSG:4326")
    username = os.getenv("pg_username")
    password = os.getenv("pg_pass")
    host = os.getenv("pg_host")
    db = "start_db"
    table_name = "roma"
    engine = create_engine(f"postgresql://{username}:{password}@{host}:5432/{db}")
    h3_grid.to_postgis(table_name, engine, if_exists="append",index=True)
    shutil.rmtree(out_dir)
    logger.info(f" -- Data sent to {table_name} table ({len(h3_grid)} hexagons)")

if __name__ == "__main__":
    import sys
    s2_to_h3("32TQM","20220902",res=int(sys.argv[1]), simulate=False)