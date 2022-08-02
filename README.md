# DGGS TBX

## Description
Tools to create and manage Discrete Global Grid Systems

## Installation
```bash
pip install .
```

## Usage
### Create H3 grid from a raster
```bash
Usage: main.py cog2h3 [OPTIONS] RASTER_PATH RESOLUTION OUT_DIR
```
```bash
python src/dggs_tbx/main.py cog2h3 ../../S2_DATA/S2B_14QMF_20220725_0_L2A/B08.tif 5 .
```
### Create rHEALpix grid from raster
```bash
Usage: main.py cog2rpix [OPTIONS] RASTER_PATH RESOLUTION OUT_DIR
```
```bash
python src/dggs_tbx/main.py cog2rpix ../../S2_DATA/S2B_14QMF_20220725_0_L2A/B08.tif 5 .
```


## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

* Integrate DGGRID
* Create docker image

## Authors and acknowledgment
Based on the work of Alex Kmoch


## Project status
_Very_ early beginnings 
