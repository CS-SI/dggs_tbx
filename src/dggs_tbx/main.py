import logging
from logging import INFO
from pathlib import Path
from tempfile import gettempdir
from typing import List

import typer
from rich.logging import RichHandler

from dggs_tbx.h3_tbx import h3_from_raster_extent, s2_to_h3
from dggs_tbx.rpix_tbx import rpix_from_raster_extent
from dggs_tbx.utils import binary_scl, rasterval_geojson

FORMAT = "%(message)s"
logging.basicConfig(level=INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

logger = logging.getLogger(__name__)

app = typer.Typer()

bands_10m = ["B02", "B03", "B04", "B08"]


@app.command()
def raster2h3(raster_path: Path, resolution: int, out_dir: Path):
    df_path = h3_from_raster_extent(raster_path, out_dir, resolution)
    rasterval_geojson(df_path, raster_path)


@app.command()
def raster2rpix(raster_path: Path, resolution: int, out_dir: Path):
    df_path = rpix_from_raster_extent(raster_path, out_dir, resolution)
    rasterval_geojson(Path(df_path), raster_path)


@app.command()
def sclindex(raster_path: Path, resolution: int, out_dir: Path):
    raster_fn = raster_path.parent / Path(raster_path.name + "_bin.tif")
    binary_scl(raster_path, raster_fn)
    df_path = h3_from_raster_extent(raster_fn, out_dir, resolution)
    rasterval_geojson(df_path, raster_path)


@app.command()
def cog2h3db(
    s2_tile_id: str,
    date: str,
    tmp_dir: Path = Path(gettempdir()),
    res: int = 7,
    simulate: bool = False,
    use_dask: bool = False,
    table_name: str = "test_table",
    bands=None,
) -> None:
    if bands is None:
        bands = bands_10m
    s2_to_h3(s2_tile_id, date, table_name, bands, tmp_dir, res, simulate, use_dask)


if __name__ == "__main__":
    app()
