# OpenCycleExport

Python tool to export OpenStreetMap cycle routes as GPX tracks

## Overview

Cycle routes are stored in OpenStreetMap as relations, which group together a number of ways that define the cycle route. Due to direction of travel restrictions on certain roads, roundabouts for example, cycle routes cannot easily be downloaded as continuous GPX tracks. The aim of this repository is to make a tool which can be used to download continuous GPX tracks for any cycle route contained within OpenStreetMap.

## Usage

To get started please clone the repository and install dependencies (we recommend using a virtual environment).

```
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
```

## Sub Modules

OpenCycleExport uses a number of sub modules for downloading, processing and exporting of cycle route data.

### Route Downloader

Query the OverpassAPI using [Overpass API python wrapper](https://github.com/mvexel/overpass-api-python-wrapper) to download and cache the ways contained within a cycle route relation.

### Route Processor

Process a route to compute a ordered list of points which are the best means to travel between two locations.

### Shapely Utilities

Utility functions to augment the [Shapely](https://github.com/Toblerity/Shapely) library. This allows a collection of LineStrings which make up a cycle route to be processed. LineStrings can be split where other routes join them at a mid point.

### Track Exporter

Add elevation data and export GPX tracks using [gpxpy](https://github.com/tkrajina/gpxpy).

## Licence

OpenCycleExport is licensed under the [GNU GPLv3](https://choosealicense.com/licenses/gpl-3.0/) license.
