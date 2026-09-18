import Fastify from "fastify";
import { geocodeRoute } from "./routes/geocode.js";

const app = Fastify({ logger: true });
await app.register(geocodeRoute);
await app.listen({ port: Number(process.env.PORT ?? 3000), host: "0.0.0.0" });
