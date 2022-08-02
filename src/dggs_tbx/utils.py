import logging
from pathlib import Path

import fiona
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.mask import mask
from rich.logging import RichHandler
from rich.progress import track

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def rasterval_geojson(path_to_geojson, raster_path):
    rast_vals = []
    band_name = path_to_geojson.stem
    out_geojson = path_to_geojson.parent / Path(
        str(path_to_geojson.stem) + "_filled.geojson"
    )
    logger.info(f"-- Filling {path_to_geojson}")
    count = 0
    with fiona.open(path_to_geojson, "r") as geofile:
        shapes = [feature["geometry"] for feature in geofile]
        target = len(shapes)
        # extract the raster values values within the polygon
        for i in track(range(len(shapes))):
            with rasterio.open(raster_path) as src:
                try:
                    out_image, out_transform = mask(src, [shapes[i]], crop=True)
                    rast_vals.append(int(np.mean(out_image)))
                    count+=1
                except:
                    #logger.warning("Mask outside raster extent or nodata")
                    rast_vals.append(0)
    gdf = gpd.read_file(path_to_geojson)
    gdf[band_name] = rast_vals
    #gdf = gdf.to_crs("EPSG:4326")
    gdf.to_file(out_geojson, driver="GeoJSON")
    logger.info(f"-- Updated geojson saved to: {out_geojson}")
    logger.info(f"-- Cells with value: {count}/{target}")

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