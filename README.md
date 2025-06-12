# DGGS TBX

## Description

The DGGS Toolbox, has been developed by ESA in the framework of the EU Copernicus programme (https://www.copernicus.eu/).
The main goal of DGGS Toolbox is to create and manage [Discrete Global Grid Systems (DGGS)](https://docs.ogc.org/as/20-040r3/20-040r3.html). These scripts have been written during phases 1 and 2 of the DGGS study and the outcomes are summarized in the document here enclosed in this project: [https://github.com/CS-SI/dggs_tbx/tree/main/docs](https://github.com/CS-SI/dggs_tbx/tree/main/docs)

A DGGS demonstrator is currently being developped, on the basis of the findings of the Phase 1 and 2 study.
The preliminar version is available on the Creodias platform: [DGGS Demonstrator](https://s2mpc-dggs.csgroup.space/demo/)

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

Here, the source image is in the current folder, which is mounted on /data
inside the container. Output geojson files are generated in the "output"
subfolder.

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

Here, the source image is in the current folder, which is mounted on /data
inside the container. Output geojson files are generated in the "output"
subfolder.

```bash
mkdir -p output
docker run --mount src="$(pwd)",target=/data,type=bind \
dggs_tbx raster2rpix ./S2_DATA/S2B_14QMF_20220725_0_L2A/B08.tif 5 . /data/output/
```

## Copyright and license

Copyright (C) 2024-2025 CS GROUP, [https://cs-soprasteria.com](https://cs-soprasteria.com)

DGGS Toolbox is free software. You can redistribute it and/or modify it under
the terms of the **GNU Lesser General Public License (GNU LGPL)** as published
by the Free Software Foundation, either version 3.0 of the license, or (at
your option) any later version.

SPDX-License-Identifier: LGPL-3.0-or-later

A copy of the GNU Lesser General Public License version 3.0 (GNU LGPL v3.0) is
provided in the file [COPYING.LESSER](COPYING.LESSER). Since the GNU LGPL v3.0
is a set of additional permissions on top of the GNU General Public License
version 3.0 (GNU GPL v3.0), a copy of the latter is required to fully
understand the terms and conditions. You can find it in the file
[COPYING](COPYING).

## Authors and acknowledgment

You will find the list of contributors in the [AUTHORS.md](AUTHORS.md) file.

Their work is based on the scientific work of Alexander Kmoch and Kevin Sahr
on DGGS.

## Project status

_Very_ early beginnings
