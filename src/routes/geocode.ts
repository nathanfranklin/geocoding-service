import type { FastifyPluginAsyncTypebox } from "@fastify/type-provider-typebox";
import { Type } from "@sinclair/typebox";
import { detect } from "../detect.js";
import { toFeatureCollection } from "../geojson.js";
import { forward } from "../queries/forward.js";
import { reverse, REVERSE_LAYERS } from "../queries/reverse.js";

const LAYERS = ["admin", "place"];

const Querystring = Type.Object({
  q: Type.String({ minLength: 1, description: 'place name, or "lon,lat" for reverse' }),
  mode: Type.Optional(Type.Union([Type.Literal("forward"), Type.Literal("reverse")])),
  types: Type.Optional(Type.String({ description: "comma list of layers: admin,place" })),
  limit: Type.Optional(Type.Integer({ minimum: 1, maximum: 50, default: 10 })),
});

export const geocodeRoute: FastifyPluginAsyncTypebox = async (app) => {
  app.get("/geocode", { schema: { querystring: Querystring } }, async (req, reply) => {
    const layers = req.query.types ? req.query.types.split(",") : LAYERS;
    const bad = layers.filter((l) => !LAYERS.includes(l));
    if (bad.length) return reply.code(400).send({ error: `unknown types: ${bad.join(",")}` });

    const parsed = detect(req.query.q);
    const kind = req.query.mode ?? parsed.kind;
    if (kind === "reverse" && parsed.kind !== "reverse") {
      return reply.code(400).send({ error: "mode=reverse needs q=lon,lat" });
    }

    const rows =
      kind === "reverse" && parsed.kind === "reverse"
        ? await reverse(parsed.lon, parsed.lat, layers.filter((l) => REVERSE_LAYERS.includes(l)))
        : await forward(parsed.kind === "forward" ? parsed.text : req.query.q, layers, req.query.limit ?? 10);

    return toFeatureCollection(rows);
  });
};
