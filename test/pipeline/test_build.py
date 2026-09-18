import csv
import io
import sys
from pathlib import Path

import pytest

from pipeline import build

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "test/fixtures/galway-center.osm.pbf"

csv.field_size_limit(sys.maxsize)


@pytest.fixture(scope="module")
def rows():
    buf = io.StringIO()
    build.main(str(FIXTURE), out=buf)
    return list(csv.DictReader(io.StringIO(buf.getvalue()), delimiter="\t"))


def by_name(rows, layer, name):
    return next(r for r in rows if r["layer"] == layer and r["name"] == name)


def test_layers_present(rows):
    assert {r["layer"] for r in rows} == {"admin", "place"}


def test_galway_city(rows):
    galway = by_name(rows, "place", "Galway")
    assert galway["type"] == "city"
    assert galway["place_rank"] == "16"
    assert galway["country_code"] == "IE"


def test_galway_context_chain(rows):
    context = by_name(rows, "place", "Galway")["context"].split("|")
    assert context[-1] == "Ireland"
    assert "County Galway" in context
    assert "Connacht" in context


def test_admin_row_has_polygon_and_parents(rows):
    county = by_name(rows, "admin", "County Galway")
    assert county["place_rank"] == "12"  # 2 x admin_level 6
    assert county["full_geom_wkt"].startswith(("POLYGON", "MULTIPOLYGON"))
    assert county["context"].split("|") == ["Connacht", "Ireland"]


def test_irish_alt_name_kept(rows):
    assert "Gaillimh" in by_name(rows, "place", "Galway")["alt_names"].split("|")
