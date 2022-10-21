import json
import logging
import shutil
from logging import INFO
from pathlib import Path
from tempfile import gettempdir
from typing import List

import dask.dataframe as dd
import geopandas as gpd
import h3pandas
import numpy as np
import rasterio.rio.mask
from h3 import h3
from rich.logging import RichHandler
from rich.progress import track
from shapely.geometry import Polygon, box
from utils import db_connect

from dggs_tbx.utils import down_s2

FORMAT = "%(message)s"
logging.basicConfig(level=INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

logger = logging.getLogger(__name__)
logger.setLevel(INFO)


def h3_from_raster_extent(
    raster_path: Path, output_grid: Path, resolution: int, df_ret=False
):
    with rasterio.open(raster_path, "r") as ds:
        bounds = ds.bounds
        extent_geom = box(*bounds)
        df = gpd.GeoDataFrame({"id": 1, "geometry": [extent_geom]})
        df.crs = ds.crs
        df = df.to_crs("EPSG:4326")
        logger.info(f"-- H3 at resolution {resolution}")
        out_fname = f"{raster_path.stem}_H3_res_{resolution}_ap7.geojson"
        gdf = df.h3.polyfill_resample(resolution)
        gdf = gdf.to_crs(f"EPSG:{ds.crs.to_epsg()}")
        if df_ret:
            return gdf
        else:
            gdf.to_file(output_grid / out_fname, driver="GeoJSON")
            logger.info(f"-- Grid saved to: {output_grid / out_fname}")
            return output_grid / out_fname


def s2_to_h3(
    s2_tile_id: str,
    date: str,
    table_name: str,
    bands: List,
    tmp_dir: Path = Path(gettempdir()),
    res: int = 7,
    simulate: bool = False,
    use_dask: bool = False,
):
    # Get all 10m tif files and store them in tmp dir
    # for each H3 cell load info from all bands
    # send dataframe to postgis

    # Download the Sentinel-2 data
    if simulate:
        # In case of simulation, download only one band for extent
        out_dir = down_s2(s2_tile_id, date, tmp_dir, bands=bands[0])
    else:
        out_dir = down_s2(s2_tile_id, date, tmp_dir, bands=bands)
    # Create a gdf of H3 hex at a given resolution
    list_bands = list(out_dir.rglob("*.tif"))
    if use_dask:
        logger.info("-- Using H3 library with Dask")
        h3_grid = dask_h3_from_raster(list_bands[0], out_dir, res, df_ret=True)
    else:
        logger.info("-- Using H3 pandas")
        h3_grid = h3_from_raster_extent(list_bands[0], out_dir, res, df_ret=True)
    band_values = {}
    if simulate:
        logger.info("-- Simulation is ON, using uniform distribution")
        for band in bands:
            h3_grid[band] = np.random.uniform(0, 10000, h3_grid.shape[0]).astype(int)
    else:
        # Fill the H3 dataframe
        for sat_band_path in track(list_bands):
            band_name = sat_band_path.parts[-1].replace(".tif", "")
            band_values[band_name] = []
            with rasterio.open(sat_band_path, "r") as src:
                shapes = [geom for geom in h3_grid.geometry]
                for shape in shapes:
                    try:
                        out_image, out_transform = rasterio.mask.mask(
                            src, [shape], True
                        )
                        sub_data = int(np.mean(out_image))
                        band_values[band_name].append(sub_data)
                    except:
                        logger.warning("Shape outside raster")
                        band_values[band_name].append(0)
        for band_val in band_values:
            h3_grid[band_val] = band_values[band_val]
    h3_grid["simulated"] = simulate
    h3_grid["resolution"] = res
    # Add grid name
    h3_grid["grid_name"] = "H3"
    # add column with the resolution
    h3_grid = h3_grid.to_crs("EPSG:4326")
    engine = db_connect()
    logger.info("-- Connected to DB, pushing data")
    h3_grid.to_postgis(table_name, engine, if_exists="append", index=True)
    shutil.rmtree(out_dir)
    logger.info(f" -- H3 data sent to {table_name} table ({len(h3_grid)} Cells)")


def dask_h3_from_raster(
    raster_path: Path,
    output_grid: Path,
    resolution: int,
    df_ret=False,
    dask_partition=4,
):
    out_fname = f"{raster_path.stem}_H3_res_{resolution}_ap7.geojson"
    logger.info(f"H3 at resolution {resolution}")
    with rasterio.open(raster_path, "r") as ds:
        bounds = ds.bounds
        extent_geom = box(*bounds)
        df = gpd.GeoDataFrame({"id": 1, "geometry": [extent_geom]})
        df.crs = ds.crs
        df = df.to_crs("EPSG:4326")
        logger.info(f"-- Getting extent from raster")
        map_json = df.to_json()
        map_json = json.loads(map_json)
        aoi = map_json["features"][0]["geometry"]
        logger.info(f"-- Start query hexagon ids within area")
        idx = h3.polyfill(aoi, res=resolution)
        logger.info(f"-- Done getting H3 hex ids")
        logger.info(f"-- Adding geometry to H3 hex ids")
        dest = gpd.GeoDataFrame(columns=["h3id", "geometry"], geometry="geometry")
        dest["h3id"] = list(idx)
        ddf = dd.from_pandas(dest, npartitions=dask_partition)
        ddf_applied = ddf["h3id"].apply(
            lambda row: Polygon(h3.h3_to_geo_boundary(row)), meta=(dest.columns)
        )
        ddf_applied.compute()
        dest["geometry"] = ddf_applied
        dest.crs = "EPSG:4326"
        logger.info(f"-- Done Adding geometry to H3 hex ids")
        if df_ret:
            return dest
        else:
            dest.to_file(output_grid / out_fname, driver="GeoJSON")
            logger.info(f"-- Grid saved to: {output_grid / out_fname}")
            return output_grid / out_fname


if __name__ == "__main__":
    import sys
    from pathlib import Path

    """
    if sys.argv[1] == "dask":
        df = dask_h3_from_raster(Path("../../S2_DATA/S2B_30TXQ_20220724_0_L2A/30TXQ/B02.tif"), Path("."), resolution=int(sys.argv[2]),
                                 df_ret=True)
    else:
        df = h3_from_raster_extent(Path("../../S2_DATA/S2B_30TXQ_20220724_0_L2A/30TXQ/B02.tif"), Path("."), resolution=int(sys.argv[2]),
                                 df_ret=True)
    print(df)
    """
    s2_to_h3(
        "32TQM",
        "20220902",
        "roma_H3",
        res=int(sys.argv[1]),
        simulate=True,
        use_dask=True,
    )
