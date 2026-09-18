export interface PlaceRow {
  id: number;
  osm_type: string;
  osm_id: string;
  layer: string;
  class: string;
  type: string | null;
  name: string;
  place_rank: number;
  importance: number;
  context: string[];
  country_code: string | null;
  geometry: { type: "Point"; coordinates: [number, number] };
  rank?: number;
}
