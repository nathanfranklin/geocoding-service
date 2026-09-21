from pathlib import Path

import pytest

from _util import build_rows, by_name

FIXTURE = Path(__file__).resolve().parents[2] / "test" / "fixtures" / "zurich-center.osm.pbf"


@pytest.fixture(scope="module")
def rows():
    return build_rows(FIXTURE)


def test_zurich_city(rows):
    z = by_name(rows, "place", "Zürich")  # local name keeps the umlaut
    assert z["type"] == "city"
    assert z["country_code"] == "CH"


def test_zurich_context_reaches_country(rows):
    assert by_name(rows, "place", "Zürich")["context"].split("|")[-1] == "Switzerland"