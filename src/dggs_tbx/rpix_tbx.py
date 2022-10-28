import itertools
import logging
import shutil
from pathlib import Path
from tempfile import gettempdir

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import rasterio.rio.mask
from pyproj import CRS, transform
from rhealpixdggs.dggs import WGS84_003
from rich.logging import RichHandler
from rich.progress import track
from shapely.geometry import Polygon

from dggs_tbx.utils import db_connect, down_s2

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()]
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Credit: https://github.com/allixender/dggs_t1/blob/master/more_grids.ipynb


def create_cells(res: int, extent: tuple = None):
    # Credit: https://github.com/allixender/dggs_t1/blob/master/more_grids.ipynb
    rdggs = WGS84_003
    if extent is not None:
        nw, se = extent
        ids = rdggs.cells_from_region(res, nw, se, plane=False)
        set_hex = list(itertools.chain(*ids))
    else:
        set_hex = [x for x in rdggs.grid(res)]
    df = pd.DataFrame({"cell_id": set_hex})
    logger.info(f"Done creating rHEALpix cells at res {res}")
    return df


def add_geom_cell(df):
    # Credit: https://github.com/allixender/dggs_t1/blob/master/more_grids.ipynb
    gdf = gpd.GeoDataFrame(df.copy())
    gdf["geometry"] = gdf["cell_id"].apply(
        lambda x: Polygon(x.boundary(n=3, plane=False))
    )
    gdf.crs = "EPSG:4326"
    gdf["cell_id"] = gdf["cell_id"].apply(lambda x: str(x))
    return gdf


def check_crossing(lon1: float, lon2: float, validate: bool = True):
    """
    Assuming a minimum travel distance between two provided longitude coordinates,
    checks if the 180th meridian (antimeridian) is crossed.
    """
    # Credit: https://github.com/allixender/dggs_t1/blob/master/more_grids.ipynb
    if validate and any(abs(x) > 180.0 for x in [lon1, lon2]):
        raise ValueError("longitudes must be in degrees [-180.0, 180.0]")
    return abs(lon2 - lon1) > 180.0


def check_for_geom(geom):
    # Credit: https://github.com/allixender/dggs_t1/blob/master/more_grids.ipynb
    crossed = False
    p_init = geom.exterior.coords[0]

    for p in range(1, len(geom.exterior.coords)):
        px = geom.exterior.coords[p]

        if check_crossing(p_init[0], px[0]):
            crossed = True
        p_init = px

    return crossed


def reproject_bounds(bounds, epsg_in, epsg_out="4326"):
    nw = (bounds[0], bounds[-1])
    se = (bounds[2], bounds[1])
    inProj = CRS(f"epsg:{epsg_in}")
    outProj = CRS(f"epsg:{epsg_out}")
    nw_proj = transform(inProj, outProj, nw[0], nw[1])
    se_proj = transform(inProj, outProj, se[0], se[1])
    return tuple(reversed(nw_proj)), tuple(reversed(se_proj))


def rpix_from_raster_extent(raster_path, out_dir, resolution, df_ret=False):
    with rasterio.open(raster_path) as ds:
        bounds = ds.bounds
        nw, se = reproject_bounds(bounds, ds.crs.to_epsg())
        logger.info(f"-- Grid extent : {(nw,se)}")
        epsg = ds.crs.to_epsg()
    df = create_cells(resolution, extent=(nw, se))
    grid = add_geom_cell(df)
    # grid['crossed'] = grid['geometry'].apply(check_for_geom)
    # grid = grid.loc[grid['crossed'] == False]
    grid = grid.to_crs(f"EPSG:{epsg}")
    if df_ret:
        return grid
    else:
        out_fname = f"{raster_path.stem}_rpix_res_{resolution}.geojson"
        logger.info(f"Try to save output file {out_fname}")
        grid.to_file(out_dir / out_fname, driver="GeoJSON")
        return out_dir / out_fname


def s2_to_rpix(
    s2_tile_id: str, date="str", tmp_dir=Path(gettempdir()), res=7, simulate=False
):
    # Get all 10m tif files and store them in tmp dir
    # for each rpix cell load info from all bands
    # send dataframe to postgis
    # Download the Sentinel-2 data
    bands = ["B02", "B08"]
    out_dir = down_s2(s2_tile_id, date, tmp_dir, bands=bands)
    # Create a gdf of rpix at a given resolution
    list_bands = list(out_dir.rglob("*.tif"))
    rpix_grid = rpix_from_raster_extent(list_bands[0], out_dir, res, df_ret=True)
    if simulate:
        logger.info("-- Simulation is ON")
        for band in bands:
            rpix_grid[band] = [None] * rpix_grid.shape[0]
    else:
        # Fill the H3 dataframe
        band_values = {}
        for sat_band_path in track(list_bands):
            band_name = sat_band_path.parts[-1].replace(".tif", "")
            band_values[band_name] = []
            with rasterio.open(sat_band_path, "r") as src:
                shapes = [geom for geom in rpix_grid.geometry]
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
            rpix_grid[band_val] = band_values[band_val]
    # Add resolution column
    rpix_grid["resolution"] = res
    # Add grid name
    rpix_grid["grid_name"] = "rpix"
    # Reproject to 4326 for visualisation
    rpix_grid = rpix_grid.to_crs("EPSG:4326")
    # Send data to Postgis DB
    table_name = "roma_rpix"
    db = "DGGS"
    engine = db_connect(db)
    rpix_grid.to_postgis(table_name, engine, if_exists="append", index=True)
    shutil.rmtree(out_dir)
    logger.info(f" -- Rpix data sent to {table_name} table ({len(rpix_grid)} cells)")


if __name__ == "__main__":
    import sys

    s2_to_rpix("32TQM", "20220902", res=int(sys.argv[1]), simulate=True)
