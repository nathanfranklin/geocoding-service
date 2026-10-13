"""Shared helpers for the pipeline tests: build a fixture into rows, then look them up."""

from pipeline import build


def build_rows(fixture_path):
    """Run the pipeline on a fixture PBF and return its rows as dicts (native values)."""
    return list(build.rows(str(fixture_path)))


def by_name(rows, layer, name):
    """The single row in a layer with this exact name."""
    return next(r for r in rows if r["layer"] == layer and r["name"] == name)


def pois(rows, name):
    """All POI rows with this name (OSM often has several objects sharing a name)."""
    return [r for r in rows if r["layer"] == "poi" and r["name"] == name]
