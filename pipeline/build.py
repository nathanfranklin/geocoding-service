"""Build places.tsv from an OSM PBF.

Each row gets its context: the admin boundaries containing it (Galway → County Galway → Connacht → Ireland).
That needs the boundaries first, so the file is read twice:

  pass 1  admin boundaries -> polygons in an STRtree (log-time containment lookups)
  pass 2  place=* nodes    -> one TSV row each, with context from pass 1

Both are pyosmium SimpleHandlers: apply_file() streams the PBF and calls node()/area() per object.
See later TODO about FileProcessor.

Layers written: admin, place.  TODO: poi, street.
"""

import csv
import sys

import osmium
from osmium import geom as og
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

wkb_factory = og.WKBFactory()  # converts osmium areas to WKB, which shapely can load


def importance(place_rank):
    """0–1 score for ranking results; purely from rank for now.

    TODO: population tag, Wikipedia link counts, click feedback.
    """
    return max(0.05, 0.75 - place_rank / 40.0)


def alt_names(tags, name):
    """Get other-language names (name:* tags), minus the display name."""
    return sorted({v for k, v in tags if k.startswith("name:") and v != name})


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


def context_of(boundaries):
    """Build a place's context from the boundaries around it: their names, plus the country's two-letter code."""
    ctx = [b["name"] for b in boundaries]
    cc = next((b["country_code"] for b in boundaries if b["admin_level"] == 2), None)
    return ctx, cc


class Places(osmium.SimpleHandler):
    """One TSV row per named place=* node."""

    def __init__(self, boundaries, tsv):
        super().__init__()
        self.boundaries, self.tsv = boundaries, tsv

    def node(self, n):
        t = n.tags
        if "name" not in t or t.get("place") not in PLACE_RANK:
            return
        pt = Point(n.location.lon, n.location.lat)
        rank = PLACE_RANK[t["place"]]
        ctx, cc = context_of(self.boundaries.containing(pt))
        self.tsv.writerow(
            [
                "N",
                n.id,
                "place",
                "place",
                t["place"],
                t["name"],
                "|".join(alt_names(t, t["name"])),
                f"{pt.x:.6f}",
                f"{pt.y:.6f}",
                rank,
                f"{importance(rank):.3f}",
                "|".join(ctx),
                cc or "",
                "",
            ]
        )


def main(path, out=sys.stdout):
    # TODO: separate row generation from TSV writing so tests can inspect dicts instead of parsing CSV

    # Pass 1: read the file, keep admin boundaries, index them
    admin_boundaries = AdminBoundaries()
    admin_boundaries.apply_file(path, locations=True)
    admin_boundaries.build_index()
    print(f"pass 1: {len(admin_boundaries.polygons)} admin boundaries", file=sys.stderr)

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

    # Write a row for each admin boundary, with all the boundaries above it as context.
    for polygon, meta in zip(admin_boundaries.polygons, admin_boundaries.meta):
        # TODO: use admin_centre/label member node instead of representative_point()
        pt = polygon.representative_point()
        parents = [b for b in admin_boundaries.containing(pt) if b["admin_level"] < meta["admin_level"]]
        ctx, cc = context_of(parents)
        rank = 2 * meta["admin_level"]
        tsv.writerow(
            [
                meta["osm_type"],
                meta["osm_id"],
                "admin",
                "boundary",
                "administrative",
                meta["name"],
                "|".join(meta["alt_names"]),
                f"{pt.x:.6f}",
                f"{pt.y:.6f}",
                rank,
                f"{importance(rank):.3f}",
                "|".join(ctx),
                meta["country_code"] or cc or "",
                polygon.wkt,
            ]
        )

    # Pass 2: read again, one row per place node. (locations=True only needed once area()/way() are added)
    # TODO: use osmium.FileProcessor instead of SimpleHandler so the library can prefilter nodes
    Places(admin_boundaries, tsv).apply_file(path, locations=True)


if __name__ == "__main__":
    main(sys.argv[1])
