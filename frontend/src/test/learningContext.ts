import { vi } from "vitest";

import { useLearning } from "../contexts/LearningContext";
import { activityContent, learner, processedInteraction, recommendation, resource, selection, state } from "./fixtures";

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
    online: true,
    pending: 0,
    loading: false,
    error: null,
    syncError: null,
    loadLearners: vi.fn().mockResolvedValue(undefined),
    selectLearner: vi.fn().mockResolvedValue(undefined),
    createLearner: vi.fn().mockResolvedValue(undefined),
    refresh: vi.fn().mockResolvedValue(undefined),
    loadActivity: vi.fn().mockResolvedValue({ payload: activityContent, source: "network" }),
    submitAnswer: vi.fn().mockResolvedValue(processedInteraction),
    ...overrides,
  };
}
