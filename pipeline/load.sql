-- loads places.tsv (i.e drops and recreates places table)

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

DROP TABLE IF EXISTS places_stage;
CREATE TEMP TABLE places_stage (
  osm_type char(1), osm_id bigint, layer text, class text, type text, name text,
  alt_names text, lon double precision, lat double precision,
  place_rank int, importance float, context text, country_code text, full_geom_wkt text
);
COPY places_stage FROM :'tsv' WITH (FORMAT csv, DELIMITER E'\t', HEADER true, QUOTE E'\x01');  -- no quoting; names may contain "

DROP TABLE IF EXISTS places;
CREATE TABLE places (
  id            bigserial PRIMARY KEY,
  osm_type      char(1)  NOT NULL,
  osm_id        bigint   NOT NULL,
  layer         text     NOT NULL,
  class         text     NOT NULL,
  type          text,
  name          text     NOT NULL,
  name_norm     text     NOT NULL,                              -- lowercased, unaccented; what the trigram index and forward query use
  alt_names     text[],
  geom          geometry(Point, 4326) NOT NULL,
  full_geom     geometry(Geometry, 4326),
  place_rank    int      NOT NULL,
  importance    float    NOT NULL,
  context       text[]   NOT NULL DEFAULT '{}',
  country_code  text
);

INSERT INTO places (osm_type, osm_id, layer, class, type, name, name_norm, alt_names, geom, full_geom,
                    place_rank, importance, context, country_code)
SELECT osm_type, osm_id, layer, class, NULLIF(type, ''), name,
       lower(unaccent(regexp_replace(btrim(name), '\s+', ' ', 'g'))),
       NULLIF(string_to_array(alt_names, '|'), '{}'),
       ST_SetSRID(ST_MakePoint(lon, lat), 4326),
       CASE WHEN full_geom_wkt = '' THEN NULL ELSE ST_SetSRID(ST_GeomFromText(full_geom_wkt), 4326) END,
       place_rank, importance,
       COALESCE(string_to_array(context, '|'), '{}'),           -- COPY reads an empty field as NULL
       NULLIF(country_code, '')
FROM places_stage;

CREATE INDEX places_geom_gist      ON places USING gist (geom);                                   -- reverse: nearest point
CREATE INDEX places_full_geom_gist ON places USING gist (full_geom) WHERE full_geom IS NOT NULL;  -- reverse: containment (admin only for now; TODO poi areas, streets)
CREATE INDEX places_name_trgm      ON places USING gin  (name_norm gin_trgm_ops);                 -- forward: fuzzy + prefix
ANALYZE places;

SELECT layer, count(*) FROM places GROUP BY layer ORDER BY min(place_rank);
