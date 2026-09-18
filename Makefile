.PHONY: help get-data clean-data up up-foreground down build-galway build-zurich build-ireland build-switzerland build load test lint format

.DEFAULT_GOAL := help

help:                     # list targets
	@grep -E '^[a-z-]+:.*#' $(MAKEFILE_LIST) | sed 's/:.*#/ —/'

# --- data
get-data:                 # download IE + CH from Geofabrik, cut city subsets, merge (~750 MB)
	pipeline/get_data.sh

clean-data:               # remove downloaded and derived data (fixtures in test/ are kept)
	rm -rf data/

# --- database
up:                       # Postgres + PostGIS in Docker, background; returns when healthy
	docker compose up -d --wait

up-foreground:            # same, with logs streaming; Ctrl-C stops it
	docker compose up

down:                     # stop the database
	docker compose down

# --- pipeline
build-galway:             # build data/places.tsv from the Galway subset (~30 s)
	uv run pipeline/build.py data/subsets/galway.osm.pbf > data/places.tsv

build-zurich:             # build data/places.tsv from the Zürich subset (~5 s)
	uv run pipeline/build.py data/subsets/zurich.osm.pbf > data/places.tsv

build-ireland:            # build data/places.tsv from all of Ireland (~1.5 min)
	uv run pipeline/build.py data/raw/ireland-and-northern-ireland-latest.osm.pbf > data/places.tsv

build-switzerland:        # build data/places.tsv from all of Switzerland (~1 min)
	uv run pipeline/build.py data/raw/switzerland-latest.osm.pbf > data/places.tsv

build:                    # build data/places.tsv from both countries (~2.5 min) — what the API ships with
	uv run pipeline/build.py data/merged/ie-ch.osm.pbf > data/places.tsv

load:                     # data/places.tsv → places table
	docker compose exec -T db psql -U geo -d geo -v tsv=/data/places.tsv -f - < pipeline/load.sql

# --- quality
test:                     # pytest
	uv run pytest

lint:                     # black --check + flake8
	uv run black --check pipeline test && uv run flake8 pipeline test

format:                   # black
	uv run black pipeline test
