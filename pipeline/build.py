"""Build places.tsv from an OSM PBF.

Each row gets its context: the admin boundaries containing it (Galway → County Galway → Connacht → Ireland).
That needs the boundaries first, so the file is read twice:

  pass 1  admin boundaries -> polygons in an STRtree (log-time containment lookups)
  pass 2  place / POI nodes and areas -> one TSV row each, with context from pass 1

Both are pyosmium SimpleHandlers: apply_file() streams the PBF and calls node()/area() per object.
See later TODO about FileProcessor.

Layers written: admin, place, poi.  TODO: street/address.
"""

import csv
import sys
from typing import NamedTuple

import osmium
from osmium import geom as og
from osmium.filter import KeyFilter
from shapely import STRtree, Point, wkb

# Nominatim's ranking convention: https://nominatim.org/release-docs/latest/customize/Ranking/
PLACE_RANK = {
    "city": 16,
    "town": 18,
    "village": 19,
    "suburb": 19,
    "hamlet": 20,
    "neighbourhood": 22,
    "locality": 22,
}

# a 30 rank for every POI
POI_RANK = 30

# All OSM primary keys that denote a POI. Source: https://wiki.openstreetmap.org/wiki/Map_features
# Except these:  highway, waterway, building, place, boundary (place/boundary are in place/admin layers)
POI_KEYS = (
    "amenity",
    "shop",
    "tourism",
    "leisure",
    "historic",
    "railway",
    "public_transport",
    "aeroway",
    "aerialway",
    "office",
    "craft",
    "healthcare",
    "emergency",
    "man_made",
    "natural",
    "sport",
    "military",
)

wkb_factory = og.WKBFactory()  # converts osmium areas to WKB, which shapely can load


def importance(place_rank: int) -> float:
    """0–1 score for ranking results; purely from rank for now.

    TODO: population tag, Wikipedia link counts, click feedback; per-class POI ranks (all fixed to 30 now).
    """
    return max(0.05, 0.75 - place_rank / 40.0)


def alt_names(tags, name):
    """Get other-language names (name:* tags), minus the display name."""
    return sorted({v for k, v in tags if k.startswith("name:") and v != name})


def get_poi_key(tags) -> str | None:
    """The first POI tag present (amenity/shop/…), or None."""
    return next((k for k in POI_KEYS if k in tags), None)


class AdminBoundaries(osmium.SimpleHandler):
    """Collects admin boundary polygons and answers "which boundaries contain this point?" for context."""

    def __init__(self):
        super().__init__()
        self.polygons, self.meta, self.tree = [], [], None

    def area(self, a):
        t = a.tags
        if t.get("boundary") != "administrative" or "name" not in t:
            return
        level = t.get("admin_level", "")
        # skip malformed values and level 1
        if not level.isdigit() or int(level) < 2:
            return
        try:
            # to shapely via WKB; buffer(0) repairs invalid rings
            polygon = wkb.loads(wkb_factory.create_multipolygon(a), hex=True).buffer(0)
        except RuntimeError as e:
            print(f"skip {a.orig_id()} {t.get('name')}: {e}", file=sys.stderr)
            return

        # Admin display name.
        # name:en gives one language per context string (Irish boundaries mix Irish, English and bilingual names)
        # TODO: collect all name:* languages into the TSV and let the API pick one (language= param)
        name = t.get("name:en", t["name"])
        self.polygons.append(polygon)
        self.meta.append(
            {
                "osm_type": "W" if a.from_way() else "R",
                "osm_id": a.orig_id(),
                "name": name,
                "admin_level": int(level),
                "country_code": t.get("ISO3166-1"),
                "alt_names": sorted(set(alt_names(t, name)) | ({t["name"]} - {name})),
            }
        )

    def build_index(self):
        """Put the collected polygons in an STRtree so containing() is a log-time lookup. Call once after apply_file."""
        self.tree = STRtree(self.polygons)

    def containing(self, pt):
        """Boundaries containing pt, deepest first."""
        hits = self.tree.query(pt, predicate="within")
        return sorted((self.meta[i] for i in hits), key=lambda m: m["admin_level"], reverse=True)


def context_of(boundaries) -> tuple[list[str], str | None]:
    """Build a place's context from the boundaries around it: their names, plus the country's two-letter code."""
    ctx = [b["name"] for b in boundaries]
    cc = next((b["country_code"] for b in boundaries if b["admin_level"] == 2), None)
    return ctx, cc


class Kind(NamedTuple):
    """How a feature is classified into a row.

    layer      place | poi | admin
    osm_class  OSM key, becomes the `class` column: place, amenity, shop, boundary
    type       OSM value, becomes the `type` column: city, pub, convenience
    rank

    examples:
         Galway     -->  Kind("place", "place",   "city",        16)
         Brusna Inn --> Kind("poi",   "amenity", "pub",         30)
    """

    layer: str
    osm_class: str
    type: str
    rank: int


def classify(tags) -> Kind | None:
    """The Kind for a tag set, or None to skip it.

    A place=* tag takes priority over a POI tag.
    """
    place = tags.get("place")
    if place in PLACE_RANK:
        return Kind("place", "place", place, PLACE_RANK[place])
    key = get_poi_key(tags)
    if key:
        return Kind("poi", key, tags[key], POI_RANK)
    return None


def _row(pt, osm_type, osm_id, layer, osm_class, typ, rank, name, alts, ctx, cc, wkt):
    """One row as a dict of native values (lists stay lists, numbers stay numbers). write_tsv() formats them."""
    return {
        "osm_type": osm_type,
        "osm_id": osm_id,
        "layer": layer,
        "class": osm_class,
        "type": typ,
        "name": name,
        "alt_names": alts,
        "lon": pt.x,
        "lat": pt.y,
        "place_rank": rank,
        "importance": importance(rank),
        "context": ctx,
        "country_code": cc,
        "full_geom_wkt": wkt,
    }


def load_boundaries(path) -> AdminBoundaries:
    """Pass 1: read the file, keep admin boundaries, index them."""
    boundaries = AdminBoundaries()
    # locations=True keeps an in-memory id->(lon,lat) cache for every node in the file, so area
    # geometries can be assembled. On a full country this cache, not the row data, is the dominant
    # memory cost.
    # SCALABILITY (later, not now): move it to a disk-backed index, e.g.
    #   boundaries.apply_file(path, locations=True, idx="sparse_file_array,nodes.cache")
    # or reuse one serialized boundary set across sharded per-tile runs. Fine in RAM at IE/CH scale.
    boundaries.apply_file(path, locations=True)
    boundaries.build_index()
    print(f"pass 1: {len(boundaries.polygons)} admin boundaries", file=sys.stderr)
    return boundaries


def _place_or_poi_row(obj, boundaries) -> dict | None:
    """Row for a named place/POI node or area, or None to skip it. name is guaranteed by the KeyFilter."""
    t = obj.tags
    kind = classify(t)
    if kind is None:
        return None
    if isinstance(obj, osmium.osm.Node):
        pt = Point(obj.location.lon, obj.location.lat)
        osm_type, osm_id = "N", obj.id
    else:  # Area (closed way or multipolygon relation)
        if t.get("boundary") == "administrative":
            return None  # admin boundaries are emitted from pass 1, not here
        try:
            pt = wkb.loads(wkb_factory.create_multipolygon(obj), hex=True).representative_point()
        except RuntimeError:
            return None
        osm_type, osm_id = ("W" if obj.from_way() else "R"), obj.orig_id()
    ctx, cc = context_of(boundaries.containing(pt))
    return _row(
        pt,
        osm_type,
        osm_id,
        kind.layer,
        kind.osm_class,
        kind.type,
        kind.rank,
        t["name"],
        alt_names(t, t["name"]),
        ctx,
        cc,
        None,
    )


def admin_rows(boundaries):
    """One row per admin boundary, with the boundaries above it as context."""
    for polygon, meta in zip(boundaries.polygons, boundaries.meta):
        # TODO: use admin_centre/label member node instead of representative_point()
        pt = polygon.representative_point()
        parents = [b for b in boundaries.containing(pt) if b["admin_level"] < meta["admin_level"]]
        ctx, cc = context_of(parents)
        rank = 2 * meta["admin_level"]
        yield _row(
            pt,
            meta["osm_type"],
            meta["osm_id"],
            "admin",
            "boundary",
            "administrative",
            rank,
            meta["name"],
            meta["alt_names"],
            ctx,
            meta["country_code"] or cc,
            polygon.wkt,
        )


def rows(path):
    """Yield every row for a PBF: admin boundaries first, then places and POIs. Native values; write_tsv() formats."""
    boundaries = load_boundaries(path)
    yield from admin_rows(boundaries)

    # Pass 2: stream places / POIs.
    # with_areas() assembles closed ways and multipolygon relations into Area objects
    # with_filter(KeyFilter("name")) drops unnamed objects.
    # A named closed way arrives as both a Way and an Area; we take the Area.
    pass2 = osmium.FileProcessor(path).with_areas().with_filter(KeyFilter("name"))
    for obj in pass2:
        if isinstance(obj, (osmium.osm.Node, osmium.osm.Area)):
            row = _place_or_poi_row(obj, boundaries)
            if row is not None:
                yield row


def write_tsv(rows, out=sys.stdout):
    """Write rows to TSV. This is the one place values get formatted (lists joined with |, None as empty)."""
    tsv = csv.writer(out, delimiter="\t", lineterminator="\n")
    tsv.writerow(
        [
            "osm_type",
            "osm_id",
            "layer",
            "class",
            "type",
            "name",
            "alt_names",
            "lon",
            "lat",
            "place_rank",
            "importance",
            "context",
            "country_code",
            "full_geom_wkt",
        ]
    )
    for r in rows:
        tsv.writerow(
            [
                r["osm_type"],
                r["osm_id"],
                r["layer"],
                r["class"],
                r["type"],
                r["name"],
                "|".join(r["alt_names"]),
                f"{r['lon']:.6f}",
                f"{r['lat']:.6f}",
                r["place_rank"],
                f"{r['importance']:.3f}",
                "|".join(r["context"]),
                r["country_code"] or "",
                r["full_geom_wkt"] or "",
            ]
        )


def main(path, out=sys.stdout):
    write_tsv(rows(path), out)


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1])
