import { pool } from "../db.js";
import type { PlaceRow } from "./row.js";

const COLS = `id, osm_type, osm_id, layer, class, type, name, place_rank, importance, context, country_code,
              ST_AsGeoJSON(geom, 6)::json AS geometry`;
const PT = `ST_SetSRID(ST_MakePoint($1, $2), 4326)`;

// One query per requested layer, run together. Admin rows are polygons — return the deepest
// (highest place_rank) one containing the point. Everything else is a point (i.e. return the nearest).
const BY_LAYER: Record<string, string> = {
  admin: `SELECT ${COLS} FROM places
          WHERE layer = 'admin' AND ST_Contains(full_geom, ${PT})
          ORDER BY place_rank DESC LIMIT 1`,
  place: `SELECT ${COLS} FROM places
          WHERE layer = 'place'
          ORDER BY geom <-> ${PT} LIMIT 1`,
};

export const REVERSE_LAYERS = Object.keys(BY_LAYER);

export async function reverse(lon: number, lat: number, layers: string[]): Promise<PlaceRow[]> {
  const results = await Promise.all(
    layers.filter((l) => l in BY_LAYER).map((l) => pool.query<PlaceRow>(BY_LAYER[l], [lon, lat])),
  );
  return results.flatMap((r) => r.rows);
}
