import { defineConfig } from "vitest/config";

export default defineConfig({
  test: { include: ["test/api/**/*.test.ts"] },
});
