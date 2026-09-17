#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

GEOFABRIK=https://download.geofabrik.de/europe
IE=ireland-and-northern-ireland-latest.osm.pbf
CH=switzerland-latest.osm.pbf

rm -rf data/raw data/subsets data/merged
mkdir -p data/{raw,subsets,merged}

echo "== download";  wget -P data/raw "$GEOFABRIK/$IE" "$GEOFABRIK/$CH"

echo "== subsets"
osmium extract -b -9.12,53.24,-8.95,53.31 "data/raw/$IE" -o data/subsets/galway.osm.pbf
osmium extract -b 8.45,47.32,8.63,47.43     "data/raw/$CH" -o data/subsets/zurich.osm.pbf

echo "== merge Ireland and Switzerland";  osmium merge "data/raw/$IE" "data/raw/$CH" -o data/merged/ie-ch.osm.pbf
echo "== done";   ls -lh data/raw data/subsets data/merged
