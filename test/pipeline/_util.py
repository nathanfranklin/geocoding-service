"""Shared helpers for the pipeline tests: build a fixture into rows, then look them up."""

import csv
import io
import sys

from pipeline import build

# Admin rows carry full polygon WKT; Ireland's coastline is multi-MB, past csv's default field cap.
csv.field_size_limit(sys.maxsize)


def build_rows(fixture_path):
    """Run the pipeline on a fixture PBF and return the TSV as a list of dict rows."""
    buf = io.StringIO()
    build.main(str(fixture_path), out=buf)
    return list(csv.DictReader(io.StringIO(buf.getvalue()), delimiter="\t"))


def by_name(rows, layer, name):
    """The single row in a layer with this exact name."""
    return next(r for r in rows if r["layer"] == layer and r["name"] == name)


def pois(rows, name):
    """All POI rows with this name (OSM often has several objects sharing a name)."""
    return [r for r in rows if r["layer"] == "poi" and r["name"] == name]
