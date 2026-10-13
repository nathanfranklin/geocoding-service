"""Build the committed Galway fixture and check place, admin, and POI rows."""

from pathlib import Path

import pytest

from _util import build_rows, by_name, pois

FIXTURE = Path(__file__).resolve().parents[2] / "test" / "fixtures" / "galway-center.osm.pbf"


@pytest.fixture(scope="module")
def rows():
    return build_rows(FIXTURE)


def test_layers_present(rows):
    assert {r["layer"] for r in rows} == {"admin", "place", "poi"}


def test_galway_city(rows):
    galway = by_name(rows, "place", "Galway")
    assert galway["type"] == "city"
    assert galway["place_rank"] == 16
    assert galway["country_code"] == "IE"


def test_galway_context_chain(rows):
    context = by_name(rows, "place", "Galway")["context"]
    assert context[-1] == "Ireland"
    assert "County Galway" in context
    assert "Connacht" in context


def test_admin_row_has_polygon_and_parents(rows):
    county = by_name(rows, "admin", "County Galway")
    assert county["place_rank"] == 12  # 2 x admin_level 6
    assert county["full_geom_wkt"].startswith(("POLYGON", "MULTIPOLYGON"))
    assert county["context"] == ["Connacht", "Ireland"]


def test_irish_alt_name_kept(rows):
    assert "Gaillimh" in by_name(rows, "place", "Galway")["alt_names"]


def test_spanish_arch_monument_is_poi(rows):
    # the monument is a building way (tests the area() path); tourism wins POI-key precedence over historic
    monument = next(r for r in pois(rows, "Spanish Arch") if r["class"] == "tourism")
    assert monument["type"] == "attraction"
    assert monument["osm_type"] == "W"
    assert "An Póirse Caoch" in monument["alt_names"]  # name:ga


def test_same_name_different_objects(rows):
    # OSM has a monument AND a bus stop both named "Spanish Arch" — both are POIs, different classes
    classes = {r["class"] for r in pois(rows, "Spanish Arch")}
    assert {"tourism", "public_transport"} <= classes


def test_power_transformer_excluded(rows):
    # a transformer named "Spanish Arch" exists in OSM, but power is not a POI key, so it is dropped
    assert "power" not in {r["class"] for r in rows}
    assert "transformer" not in {r["type"] for r in rows}
