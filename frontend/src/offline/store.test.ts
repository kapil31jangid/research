import { describe, expect, it } from "vitest";

import { curriculum } from "../test/fixtures";
import { curriculumCacheKey } from "./store";

describe("curriculum-aware offline keys", () => {
  it("separates identical activity IDs across classes", () => {
    const classFive = curriculumCacheKey(curriculum);
    const classSix = curriculumCacheKey({
      ...curriculum,
      class_level: 6,
      subject_id: "ncert-c6-mathematics",
    });
    expect(classFive).toBe("ncert:class-5:ncert-c5-mathematics");
    expect(classSix).not.toBe(classFive);
  });
});
