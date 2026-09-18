.PHONY: get-data clean-data build-galway build-zurich build-ireland build-switzerland build test lint format

get-data:
	pipeline/get_data.sh

clean-data:
	rm -rf data/raw data/subsets data/merged

build-galway:
	uv run pipeline/build.py data/subsets/galway.osm.pbf > data/places.tsv

build-zurich:
	uv run pipeline/build.py data/subsets/zurich.osm.pbf > data/places.tsv

build-ireland:
	uv run pipeline/build.py data/raw/ireland-and-northern-ireland-latest.osm.pbf > data/places.tsv

build-switzerland:
	uv run pipeline/build.py data/raw/switzerland-latest.osm.pbf > data/places.tsv

build:
	uv run pipeline/build.py data/merged/ie-ch.osm.pbf > data/places.tsv

test:
	uv run pytest

lint:
	uv run black --check pipeline test && uv run flake8 pipeline test

format:
	uv run black pipeline test
