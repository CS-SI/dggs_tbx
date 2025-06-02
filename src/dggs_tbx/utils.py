# Copyright (C) 2024-2025 CS GROUP, https://cs-soprasteria.com
#
# This file is part of DGGS Toolbox:
#
#     https://github.com/CS-SI/dggs_tbx
#
# SPDX-License-Identifier: LGPL-3.0-or-later
#
# DGGS Toolbox is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# DGGS Toolbox is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with DGGS Toolbox. If not, see
# https://www.gnu.org/licenses/.

import logging
import os
from pathlib import Path
from tempfile import gettempdir

import boto3
import fiona
import geopandas as gpd
import numpy as np
import rasterio
from botocore import UNSIGNED
from botocore.config import Config
from pyproj import CRS, transform
from rasterio.mask import mask
from rich.logging import RichHandler
from rich.progress import track
from shapely.geometry import box
from sqlalchemy import create_engine

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def rasterval_geojson(path_to_geojson, raster_path,write=True):
    rast_vals = []
    band_name = path_to_geojson.stem
    out_geojson = path_to_geojson.parent / Path(
        str(path_to_geojson.stem) + "_filled.geojson"
    )
    logger.info(f"-- Filling {path_to_geojson} with mean values from {raster_path}")
    count = 0
    with fiona.open(path_to_geojson, "r") as geofile:
        shapes = [feature["geometry"] for feature in geofile]
        target = len(shapes)
        # extract the raster values within the polygon
        for i in track(range(len(shapes))):
            with rasterio.open(raster_path) as src:
                try:
                    out_image, out_transform = mask(src, [shapes[i]], crop=True)
                    rast_vals.append(int(np.mean(out_image)))
                    count += 1
                except:
                    logger.warning("Mask outside raster extent or nodata")
                    rast_vals.append(0)
    gdf = gpd.read_file(path_to_geojson)
    gdf[band_name] = rast_vals
    # gdf = gdf.to_crs("EPSG:4326")
    if write:
        gdf.to_file(out_geojson, driver="GeoJSON")
        logger.info(f"-- Updated geojson saved to: {out_geojson}")
        logger.info(f"-- Cells with value: {count}/{target}")
    else:
        return gdf


def reproject_bounds(bounds, epsg_in, epsg_out="4326"):
    nw = (bounds[0], bounds[-1])
    se = (bounds[2], bounds[1])
    inProj = CRS(f"epsg:{epsg_in}")
    outProj = CRS(f"epsg:{epsg_out}")
    nw_proj = transform(inProj, outProj, nw[0], nw[1])
    se_proj = transform(inProj, outProj, se[0], se[1])
    return tuple(reversed(nw_proj)), tuple(reversed(se_proj))


def binary_scl(scl_file: Path, raster_fn: Path) -> None:
    """
    Convert L2A SCL file to binary cloud mask
    :param scl_file: Path to SCL file
    :param raster_fn: Output binary mask path
    """
    with rasterio.open(scl_file, "r") as src:
        scl = src.read(1)

    # Set the to-be-masked SCL values
    scl_mask_values = [0, 1, 3, 8, 9, 10, 11]

    # Set the nodata value in SCL
    scl_nodata_value = 0

    # Contruct the final binary 0-1-255 mask
    mask = np.zeros_like(scl)
    mask[scl == scl_nodata_value] = 255
    mask[~np.isin(scl, scl_mask_values)] = 1

    meta = src.meta.copy()
    meta["driver"] = "GTiff"
    dtype = rasterio.uint8
    meta["dtype"] = dtype
    meta["nodata"] = 255

    with rasterio.open(
        raster_fn,
        "w+",
        **meta,
        compress="deflate",
        tiled=True,
        blockxsize=512,
        blockysize=512,
    ) as out:
        # Modify output metadata

        out.write(mask.astype(rasterio.uint8), 1)


def get_raster_extent(raster_path: Path, outfname: Path = None) -> None:
    with rasterio.open(raster_path, "r") as ds:
        bounds = ds.bounds
        extent_geom = box(*bounds)
        df = gpd.GeoDataFrame({"id": 1, "geometry": [extent_geom]})
        df.crs = ds.crs
        df = df.to_crs("EPSG:4326")
        if outfname is None:
            outfname = raster_path.parent / Path(
                str(raster_path.name).replace(".tif", "_extent.shp")
            )
        df.to_file(outfname)
        logger.info(f"Raster extent saved to: {outfname}")


def reproject_vector(
    vector_path: Path, raster_path: Path, outfname: Path = None
) -> None:
    with rasterio.open(raster_path, "r") as ds:
        gdf = gpd.read_file(vector_path)
        logger.info(f"Reprojecting from {gdf.crs} to EPSG:{ds.crs.to_epsg()}")
        gdf = gdf.to_crs(f"EPSG:{ds.crs.to_epsg()}")
        if outfname is None:
            outfname = vector_path.parent / Path("reproj_" + str(vector_path.name))
        gdf.to_file(outfname)
        logger.info(f"Saved reprojected file to: {outfname}")
        return Path(outfname)


def down_s2(
    s2_tile_id: str, date: str, tmp_dir=Path(gettempdir()), bands=["B02", "B08"]
):
    # Download the Sentinel-2 data
    if date[5] == 0:
        month = date[6]
    else:
        month = date[5:6]
    prefix = f"sentinel-s2-l2a-cogs/{s2_tile_id[:2]}/{s2_tile_id[2:3]}/{s2_tile_id[3:]}/{date[:4]}/{month}/"
    client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    bucket_name = "sentinel-cogs"
    default_kwargs = {
        "Bucket": bucket_name,
        "Prefix": prefix,
    }
    response = client.list_objects_v2(**default_kwargs)
    contents = response.get("Contents")
    logger.info(" -- S3 response recieved")
    for resp in contents:
        key = resp["Key"]
        band = key.split("/")[-1].replace(".tif", "")
        if date in resp["Key"] and band in bands:
            product_name = key.split("/")[-2]
            out_dir = tmp_dir / product_name
            out_dir.mkdir(parents=True, exist_ok=True)
            file_name = out_dir / Path(band + ".tif")
            client.download_file(bucket_name, resp["Key"], str(file_name))
            logger.info(f" -- Saved {band} to {file_name}")
    return out_dir


def db_connect():
    db = os.getenv("pg_db", "DGGS")
    username = os.getenv("pg_username", "postgres")
    password = os.getenv("pg_pass")
    host = os.getenv("pg_host", "172.18.0.3")
    port = os.getenv("pg_port", "19432")
    engine = create_engine(f"postgresql://{username}:{password}@{host}:{port}/{db}")
    return engine
