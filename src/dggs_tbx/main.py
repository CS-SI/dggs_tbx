import logging
from logging import INFO
from pathlib import Path
import typer

from rich.logging import RichHandler
from utils import rasterval_geojson, binary_scl

from dggs_tbx.h3_tbx import h3_from_raster_extent
from dggs_tbx.rpix_tbx import rpix_from_raster_extent

FORMAT = "%(message)s"
logging.basicConfig(level=INFO, format=FORMAT, datefmt="[%X]", handlers=[RichHandler()])

logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def cog2h3(raster_path: Path, resolution: int, out_dir: Path):
    df_path = h3_from_raster_extent(raster_path, out_dir, resolution)
    rasterval_geojson(df_path, raster_path)
@app.command()
def cog2rpix(raster_path: Path, resolution: int, out_dir: Path):
    df_path = rpix_from_raster_extent(raster_path, out_dir,resolution)
    rasterval_geojson(Path(df_path), raster_path)
@app.command()
def sclindex(raster_path: Path, resolution: int, out_dir: Path):
    raster_fn = raster_path.parent / Path(raster_path.name +"_bin.tif")
    binary_scl(raster_path,raster_fn)
    df_path = h3_from_raster_extent(raster_fn, out_dir, resolution)
    rasterval_geojson(df_path, raster_path)

if __name__ =="__main__":
    app()
