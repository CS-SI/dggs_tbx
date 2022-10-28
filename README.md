# DGGS TBX

## Description
Tools to create and manage Discrete Global Grid Systems

## Quick use using docker
```bash
docker build . -t dggs_tbx
docker run dggs_tbx --help
```

## Installation
```bash
pip install .
```

## Usage
### Create H3 grid from a raster
Usage: 
```bash
dggs_tbx cog2h3 [OPTIONS] RASTER_PATH RESOLUTION OUT_DIR`
```

Sample:
```bash
dggs_tbx cog2h3 ../../S2_DATA/S2B_14QMF_20220725_0_L2A/B08.tif 5 .
```
### Create rHEALpix grid from raster
Usage: 
```bash
dggs_tbx cog2rpix [OPTIONS] RASTER_PATH RESOLUTION OUT_DIR
```

Sample:
```bash
dggs_tbx cog2rpix ../../S2_DATA/S2B_14QMF_20220725_0_L2A/B08.tif 5 .
```

## Roadmap
If you have ideas for releases in the future, it is a good idea to list them in the README.

* Integrate DGGRID
* Create docker image (add Dockerfile)

## Authors and acknowledgment
Based on the work of Alex Kmoch and Kevin Sahr


## Project status
_Very_ early beginnings 
