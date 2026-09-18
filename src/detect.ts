// Decide whether q is a coordinate pair (reverse) or text (forward).
// Coordinates are "lon,lat" — MapTiler / GeoJSON order.

export type Query =
  | { kind: "reverse"; lon: number; lat: number }
  | { kind: "forward"; text: string };

const COORD = /^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$/;

export function detect(q: string): Query {
  const m = q.match(COORD);
  if (m) {
    const lon = Number(m[1]);
    const lat = Number(m[2]);
    if (Math.abs(lon) <= 180 && Math.abs(lat) <= 90) {
      return { kind: "reverse", lon, lat};
    }
  }
  return { kind: "forward", text: normalize(q) };
}

// keep in sync with how name_norm is built in load.sql (unaccent happens Postgres-side)
export function normalize(text: string): string {
  return text.trim().replace(/\s+/g, " ").toLowerCase();
}
