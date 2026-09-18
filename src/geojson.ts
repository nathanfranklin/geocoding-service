import type { PlaceRow } from "./queries/row.js";

export const ATTRIBUTION = "© OpenStreetMap contributors (ODbL)";

export function toFeatureCollection(rows: PlaceRow[]) {
  return {
    type: "FeatureCollection" as const,
    attribution: ATTRIBUTION,
    features: rows.map((r) => ({
      type: "Feature" as const,
      id: `${r.osm_type}${r.osm_id}`,
      geometry: r.geometry,
      properties: {
        name: r.name,
        layer: r.layer,
        class: r.class,
        type: r.type,
        place_rank: r.place_rank,
        importance: r.importance,
        context: r.context,
        country_code: r.country_code,
        ...(r.rank !== undefined && { rank: Number(r.rank) }),
      },
    })),
  };
}
