import { pool } from "../db.js";
import type { PlaceRow } from "./row.js";

// Ranking: match quality × importance × layer weight.
// Admin rows are down-weighted so "galway" returns the city before its council boundary.
const SQL = `
  SELECT id, osm_type, osm_id, layer, class, type, name, place_rank, importance, context, country_code,
         ST_AsGeoJSON(geom, 6)::json AS geometry,
         GREATEST(similarity(name_norm, $1),
                  CASE WHEN name_norm LIKE $1 || '%' THEN 0.9 ELSE 0 END)
           * importance
           * CASE WHEN layer = 'admin' THEN 0.7 ELSE 1 END AS rank
  FROM places
  WHERE layer = ANY($2)
    AND (name_norm % unaccent($1) OR name_norm LIKE unaccent($1) || '%')
  ORDER BY rank DESC
  LIMIT $3`;

export async function forward(text: string, layers: string[], limit: number): Promise<PlaceRow[]> {
  const { rows } = await pool.query<PlaceRow>(SQL, [text, layers, limit]);
  return rows;
}
