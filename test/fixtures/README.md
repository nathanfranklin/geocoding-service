# Test fixtures

Small committed OSM extracts the pytest suite builds against. Each one is a **city bbox merged
with that city's parent admin boundaries, pulled whole** (first tried with a  plain bbox clips
the country/canton outlines so they never close, and then `context` and `country_code` come out
empty.)

## galway-center.osm.pbf
Galway city node, Ceannt station, Eyre Square, Spanish Arch.
Parents: Ireland (r62273), Connacht (r278721), County Galway (r335444),
Galway City council (r1390623), Galway Municipal District (r3872297).

```
    osmium extract -b -9.062,53.267,-9.043,53.277 data/raw/ireland-and-northern-ireland-latest.osm.pbf -o /tmp/galway-bbox.osm.pbf
    osmium getid -r data/raw/ireland-and-northern-ireland-latest.osm.pbf r62273 r278721 r335444 r1390623 r3872297 -o /tmp/galway-parents.osm.pbf
    osmium merge /tmp/galway-bbox.osm.pbf /tmp/galway-parents.osm.pbf -o test/fixtures/galway-center.osm.pbf
```

## zurich-center.osm.pbf
Zürich city node, Hauptbahnhof.
Parents: Schweiz (r51701, the country, carries ISO3166-1=CH), Kanton Zürich (r1690227),
Bezirk Zürich (r1690941), Zürich (r1682248).

```
    osmium extract -b 8.530,47.365,8.552,47.385 data/raw/switzerland-latest.osm.pbf -o /tmp/zurich-bbox.osm.pbf
    osmium getid -r data/raw/switzerland-latest.osm.pbf r51701 r1690227 r1690941 r1682248 -o /tmp/zurich-parents.osm.pbf
    osmium merge /tmp/zurich-bbox.osm.pbf /tmp/zurich-parents.osm.pbf -o test/fixtures/zurich-center.osm.pbf
```

## oranmore.osm.pbf
The Spar (POI on Bluebell Woods) and 28 Bluebell Woods (building, staged for the address layer).
Parents: Ireland (r62273), Connacht (r278721), County Galway (r335444),
County Galway council (r4072952), Athenry-Oranmore Municipal District (r9304197).

```
    osmium extract -b -8.940,53.258,-8.926,53.268 data/raw/ireland-and-northern-ireland-latest.osm.pbf -o /tmp/oranmore-bbox.osm.pbf
    osmium getid -r data/raw/ireland-and-northern-ireland-latest.osm.pbf r62273 r278721 r335444 r4072952 r9304197 -o /tmp/oranmore-parents.osm.pbf
    osmium merge /tmp/oranmore-bbox.osm.pbf /tmp/oranmore-parents.osm.pbf -o test/fixtures/oranmore.osm.pbf
```
