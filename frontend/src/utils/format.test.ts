import { describe, expect, it } from "vitest";

import { humanize, humanizeMisconception, latency, percent } from "./format";

describe("format helpers", () => {
  it("humanizes pathways while preserving research acronyms", () => {
    expect(humanize("bkt_based_recommendation")).toBe("BKT Based Recommendation");
    expect(humanize("lightweight_ml_recommendation")).toBe("Lightweight ML Recommendation");
  });

  it("uses friendly misconception labels and a safe fallback", () => {
    expect(humanizeMisconception("adds_denominators")).toBe("Adding denominators directly");
    expect(humanizeMisconception("new_pattern")).toBe("New Pattern");
  });

  it("formats percentages and latency consistently", () => {
    expect(percent(0.634)).toBe("63%");
    expect(latency(3.456)).toBe("3.46 ms");
    expect(latency(undefined)).toBe("—");
  });
});
