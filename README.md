# geocoding-service

Geocoding API over OpenStreetMap: forward (place name → coordinates) and reverse (coordinates → place name).

This repo was created/tested using Ireland and Switzerland data


TODO: curl examples 

## Setup

Requires `uv`, `osmium-tool` and `wget`. (TODO: docker, node)

```bash
uv sync
make get-data    # download Ireland + Switzerland extracts from Geofabrik
```


```bash
make get-data    # download Ireland + Switzerland extracts from Geofabrik, plus create Galway/Zurich subsets subsets, and create a IE/CH merged data
```

## Architecture

## Tech stack and rationale

## TODO for README

* TODO Ireland/CH choice
