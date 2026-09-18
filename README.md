# geocoding-service

A single-endpoint geocoding API over OpenStreetMap: **forward** (place name → coordinates) and
**reverse** (coordinates → place name) through one `GET /geocode`, distinguished by the input.

Built and run against Ireland and Switzerland extracts.

Responses are a GeoJSON `FeatureCollection`; each feature carries its admin `context`
(Galway → County Galway → Connacht → Ireland) and `country_code`.

## Setup

Prerequisites: `uv`, `osmium-tool`, `wget`, Docker (OrbStack or Docker Desktop), Node 22.

### Install
```bash
uv sync                       # install Python deps (pyosmium, shapely)
npm install                   # install API deps
```

### Get data and run pipeline
```bash
make get-data                 # download IE + CH from Geofabrik, cut subsets, merge (~750 MB)
make build-galway             # build data/places.tsv from the Galway subset
```

### Run service (and load tsv into database)
```bash
make up                       # start docker services (i.e. Postgres + PostGIS)
make load                     # load places.tsv into the places table
npm run dev                   # start the API on :3000
```

Then you can use API:

```bash
curl 'http://localhost:3000/geocode?q=galway'                        # forward for Galway
curl 'http://localhost:3000/geocode?q=-9.049,53.274'                 # reverse for a point near Eyre Square
curl 'http://localhost:3000/geocode?q=galway&types=place&limit=5'    # forward for Galway, settlements only, top 5
```


**Other extracts**: `make build-zurich`, `make build-ireland`, `make build-switzerland`,
`make build` (both countries, ~2.5 min). Run `make load` after any of them.
`make` on its own lists all targets.

## Architecture

The pipeline is split from the API, so main work happens at build time. `build.py` works out which admin boundaries each place sits inside and writes `data/places.tsv`. `load.sql` copies
that into an indexed `places` table in postgis.

A request is then an SQL lookup and creation of the GeoJSON FeatureCollection (the collection could be built in SQL too, but keeping it in the API keeps response
shape out of the query).
 
- **Single endpoint.** `q` as `lon,lat` is reverse, otherwise it is forward.
  - **`types`** filters layers, comma-separated (`admin`, `place`)
  - **`limit`** caps forward results.
  - **`mode=forward|reverse`** forces the direction when the input is ambiguous.
- **Layers so far:** `admin` (boundary polygons) and `place` (city/town/village nodes). TODO: `poi`, `street`.
- **Forward** ranks on name-match strength times importance, with admin boundaries down-weighted so
  `galway` returns the city above its council area.
- **Reverse** runs one query per layer: `ST_Contains` for admin polygons, nearest-point for the rest.

## Tech stack and rationale

| Layer | Choice | Why |
|---|---|---|
| API | TypeScript, Fastify | matches the target server language|
| Pipeline | Python, pyosmium, shapely | using OSM/geometry tooling, in the language I've worked in most day to day|
| Database | Postgres 18 + PostGIS + pg_trgm | one store for text (trigram) and spatial (KNN + containment) |

## Known limitations, future improvements and scaling

* Support POI/street/address layers
* Improve the importance function: currently rank-only; add population, Wikipedia/Wikidata link counts, click feedback
* Improve the pg_trgm similarity threshold; fuzzy matching picks up too much (e.g. Gals, CH for "galway").
* Better ranking: term-based relevance in Postgres (pg_search/BM25), or a separate search engine (Elasticsearch, etc.)
* Scaling: need benchmarks, move to FileProcessor or explore non-python osmium 
* API integration test with a Postgres service container in CI.

## License

Code: MIT. Data in `test/fixtures/` is © [OpenStreetMap contributors](https://www.openstreetmap.org/copyright).
