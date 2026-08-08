import { vi } from "vitest";

import { useLearning } from "../contexts/LearningContext";
import { activityContent, curriculum, learner, processedInteraction, recommendation, resource, selection, state } from "./fixtures";

type LearningContextValue = ReturnType<typeof useLearning>;

export function learningContext(
  overrides: Partial<LearningContextValue> = {},
): LearningContextValue {
  return {
    learners: [learner],
    learner,
    states: [state],
    selection,
    recommendations: [recommendation],
    resource,
    boards: [{ id: "ncert", name: "NCERT", country: "India", description: null }],
    classes: [{ board_id: "ncert", class_level: 5, content_status: "available" }],
    subjects: [{ id: curriculum.subject_id, board_id: "ncert", class_level: 5, name: "Mathematics", slug: "mathematics", description: "", content_status: "available", is_active: true, curriculum_pack_id: curriculum.curriculum_pack_id, curriculum_pack_version: curriculum.curriculum_pack_version }],
    books: [{ id: curriculum.book_id, subject_id: curriculum.subject_id, title: curriculum.book_title, source: "NCERT", language: "English", official_reference_url: null, edition: null, is_active: true }],
    chapters: [{ id: curriculum.chapter_id, book_id: curriculum.book_id, chapter_number: 2, title: curriculum.chapter_title, slug: "fractions", description: "", sequence: 2, concept_ids: [state.concept_id], is_active: true }],
    concepts: [{ id: state.concept_id, chapter_id: curriculum.chapter_id, name: "Fraction addition", description: "", difficulty: 3, mastery_threshold: .8, prerequisite_ids: [], activity_ids: [recommendation.selected_activity_id], misconception_ids: [] }],
    curriculum,
    online: true,
    pending: 0,
    loading: false,
    error: null,
    syncError: null,
    loadLearners: vi.fn().mockResolvedValue(undefined),
    selectLearner: vi.fn().mockResolvedValue(undefined),
    createLearner: vi.fn().mockResolvedValue(undefined),
    switchPathway: vi.fn().mockResolvedValue(undefined),
    refresh: vi.fn().mockResolvedValue(undefined),
    loadActivity: vi.fn().mockResolvedValue({ payload: activityContent, source: "network" }),
    submitAnswer: vi.fn().mockResolvedValue(processedInteraction),
    ...overrides,
  };
}
