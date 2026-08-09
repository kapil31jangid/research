import { IDBFactory } from "fake-indexeddb";
import { beforeEach, describe, expect, it, vi } from "vitest";

import type { InteractionCreate } from "../types";
import { activityContent, curriculum } from "../test/fixtures";
import {
  cacheActivityContent,
  cachedActivityContent,
  cachedContentMetadata,
  curriculumCacheKey,
  flushQueue,
  queuedCount,
  queueInteraction,
} from "./store";

const payload: InteractionCreate = {
  learner_id: "learner-1",
  question_id: "question-1",
  submitted_answer: "3/4",
  response_time_ms: 1200,
  hints_used: 0,
  offline: true,
  offline_content: {
    cached_activity_ids: [activityContent.activity.id],
    cached_concept_ids: [activityContent.activity.concept_id],
    cached_curriculum_keys: ["ncert:class-5:ncert-c5-mathematics"],
    app_shell_available: true,
  },
  curriculum_context: {
    board_id: curriculum.board_id,
    class_level: curriculum.class_level,
    subject_id: curriculum.subject_id,
    book_id: curriculum.book_id,
    chapter_id: curriculum.chapter_id,
    curriculum_pack_version: curriculum.curriculum_pack_version,
  },
};

describe("offline IndexedDB store", () => {
  beforeEach(() => {
    Object.defineProperty(globalThis, "indexedDB", {
      configurable: true,
      value: new IDBFactory(),
    });
  });

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

  it("separately persists educational content and reports exact metadata", async () => {
    expect(await cachedContentMetadata()).toEqual({
      activityIds: [],
      conceptIds: [],
      curriculumKeys: [],
    });
    await cacheActivityContent(activityContent);
    expect(await cachedActivityContent(activityContent.activity.id, curriculum)).toEqual(
      activityContent,
    );
    expect(await cachedContentMetadata()).toEqual({
      activityIds: [activityContent.activity.id],
      conceptIds: [activityContent.activity.concept_id],
      curriculumKeys: ["ncert:class-5:ncert-c5-mathematics"],
    });
  });

  it("deletes only successfully synchronized queue entries", async () => {
    const second = { ...payload, question_id: "question-2" };
    await queueInteraction(payload);
    await queueInteraction(second);
    expect(await queuedCount()).toBe(2);
    const interrupted = vi
      .fn<(value: InteractionCreate) => Promise<void>>()
      .mockResolvedValueOnce()
      .mockRejectedValueOnce(new Error("network interrupted"));
    await expect(flushQueue(interrupted)).rejects.toThrow("network interrupted");
    expect(await queuedCount()).toBe(1);
    const resumed = vi.fn<(value: InteractionCreate) => Promise<void>>().mockResolvedValue();
    await flushQueue(resumed);
    expect(resumed).toHaveBeenCalledWith(second);
    expect(await queuedCount()).toBe(0);
  });
});
