# DGGS TBX

## Description
Tools to create and manage Discrete Global Grid Systems

## Quick use using docker
```bash
docker build . -t dggs_tbx
docker run dggs_tbx --help
```
```text
 Usage: dggs_tbx [OPTIONS] COMMAND [ARGS]...                                    
                                                                                
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.      │
│ --show-completion             Show completion for the current shell, to copy │
│                               it or customize the installation.              │
│ --help                        Show this message and exit.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ cog2h3db      Build H3 grid from COG and store in PostgresSQL db             │
│ cog2rpixdb    Build rHEALPIx grid from COG and store in PostgresSQL db       │
│ raster2h3     Convert a raster file to H3 in GeoJSON                         │
│ raster2rpix   Convert a raster file to rHEALPix in GeoJSON                   │
│ sclindex      Create an H3 SCL index from a COG                              │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

## Usage
### Create H3 grid from a raster
Usage: 
```bash
dggs_tbx raster2h3 [OPTIONS] RASTER_PATH RESOLUTION OUT_DIR`
```

Sample:
```bash
dggs_tbx raster2h3 ./S2_DATA/S2B_14QMF_20220725_0_L2A/B08.tif 5 .
```
Sample form Docker image:

Here, the source image is in the current folder, which is mounted on /data inside the container. 
Output geojson files are generated in the "output" subfolder. 
```bash
mkdir -p output
docker run --mount src="$(pwd)",target=/data,type=bind \
dggs_tbx raster2h3 /data/S2_DATA/S2B_14QMF_20220725_0_L2A/B08.tif 5 /data/output/
```

### Create rHEALpix grid from raster
Usage: 
```bash
dggs_tbx raster2rpix [OPTIONS] RASTER_PATH RESOLUTION OUT_DIR
```

Sample:
```bash
dggs_tbx raster2rpix ./S2_DATA/S2B_14QMF_20220725_0_L2A/B08.tif 5 .
```

Sample form Docker image:

Here, the source image is in the current folder, which is mounted on /data inside the container. 
Output geojson files are generated in the "output" subfolder. 
```bash
mkdir -p output
docker run --mount src="$(pwd)",target=/data,type=bind \
dggs_tbx raster2rpix ./S2_DATA/S2B_14QMF_20220725_0_L2A/B08.tif 5 . /data/output/
```

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

* Integrate DGGRID
* Create docker image (add Dockerfile)

## Authors and acknowledgment
Based on the work of Alexander Kmoch and Kevin Sahr


## Project status
_Very_ early beginnings 
