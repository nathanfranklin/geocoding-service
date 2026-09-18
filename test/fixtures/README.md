# Test fixtures

## galway-center.osm.pbf

    osmium extract -b -9.062,53.267,-9.043,53.277 data/raw/ireland-and-northern-ireland-latest.osm.pbf -o /tmp/galway-bbox.osm.pbf
    osmium getid -r data/raw/ireland-and-northern-ireland-latest.osm.pbf r62273 r278721 r335444 r1390623 r3872297 -o /tmp/galway-parents.osm.pbf
    osmium merge /tmp/galway-bbox.osm.pbf /tmp/galway-parents.osm.pbf -o test/fixtures/galway-center.osm.pbf

## zurich-center.osm.pbf

    osmium extract -b 8.530,47.370,8.552,47.382 data/raw/switzerland-latest.osm.pbf -o /tmp/zurich-bbox.osm.pbf
    osmium getid -r data/raw/switzerland-latest.osm.pbf <ids> -o /tmp/zurich-parents.osm.pbf
    osmium merge /tmp/zurich-bbox.osm.pbf /tmp/zurich-parents.osm.pbf -o test/fixtures/zurich-center.osm.pbf
