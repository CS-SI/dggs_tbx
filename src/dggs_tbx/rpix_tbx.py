import itertools
import logging

import geopandas as gpd
import pandas as pd
import rasterio
from pyproj import CRS, transform
from rhealpixdggs.dggs import WGS84_003
from rich.logging import RichHandler
from shapely.geometry import Polygon

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


def rpix_from_raster_extent(raster_path, out_dir, resolution):
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
    out_fname = f"{raster_path.stem}_rpix_res_{resolution}.geojson"
    logger.info(f"Try to save output file {out_fname}")
    grid.to_file(out_dir / out_fname, driver="GeoJSON")
    return out_dir / out_fname

def s2_to_rpix():
    pass
