import { describe, expect, it } from "vitest";
import { detect, normalize } from "../../src/detect.js";

describe("detect", () => {
  it("treats lon,lat as reverse", () => {
    expect(detect("-9.049,53.274")).toEqual({ kind: "reverse", lon: -9.049, lat: 53.274 });
  });

  it("tolerates surrounding spaces", () => {
    expect(detect(" -9.049 , 53.274 ")).toEqual({ kind: "reverse", lon: -9.049, lat: 53.274 });
  });

  it("rejects out-of-range coordinates as forward text", () => {
    expect(detect("200,95").kind).toBe("forward");
  });

  it("treats a single number as forward", () => {
    expect(detect("12.5").kind).toBe("forward");
  });

  it("normalises forward text", () => {
    expect(detect("  Galway   City ")).toEqual({ kind: "forward", text: "galway city" });
  });
});

describe("normalize", () => {
  it("lowercases, trims, collapses whitespace", () => {
    expect(normalize("  Dún   Laoghaire ")).toBe("dún laoghaire");
  });
});