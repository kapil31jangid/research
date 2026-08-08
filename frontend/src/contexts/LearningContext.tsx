import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import {
  cacheActivityContent,
  cachedActivityContent,
  cachedContentMetadata,
  flushQueue,
  queueInteraction,
  queuedCount,
} from "../offline/store";
import { api } from "../services/api";
import type {
  ActivityContentResponse,
  ConceptState,
  InteractionResponse,
  Learner,
  LearningSelection,
  Recommendation,
  Resource,
} from "../types";

type ContentSource = "network" | "cache";
type LearningContextValue = {
  learners: Learner[];
  learner?: Learner;
  states: ConceptState[];
  selection?: LearningSelection;
  recommendations: Recommendation[];
  resource?: Resource;
  online: boolean;
  pending: number;
  loading: boolean;
  error: string | null;
  syncError: string | null;
  loadLearners: () => Promise<void>;
  selectLearner: (learner: Learner) => Promise<void>;
  createLearner: (name: string, grade: number) => Promise<void>;
  refresh: () => Promise<void>;
  loadActivity: (
    activityId: string,
  ) => Promise<{ payload: ActivityContentResponse; source: ContentSource }>;
  submitAnswer: (
    answer: string,
    hints: number,
    responseTimeMs: number,
  ) => Promise<InteractionResponse | null>;
};

const LearningContext = createContext<LearningContextValue | null>(null);

export function LearningProvider({ children }: { children: ReactNode }) {
  const [learners, setLearners] = useState<Learner[]>([]);
  const [learner, setLearner] = useState<Learner>();
  const [states, setStates] = useState<ConceptState[]>([]);
  const [selection, setSelection] = useState<LearningSelection>();
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [resource, setResource] = useState<Resource>();
  const [online, setOnline] = useState(() => navigator.onLine);
  const [pending, setPending] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  const loadLearners = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setLearners(await api.learners());
    } catch {
      setError("We couldn’t load learner profiles. Check that the RAPID-Learn API is running.");
    } finally {
      setLoading(false);
    }
  }, []);

  const loadWorkspace = useCallback(async (selected: Learner) => {
    setLoading(true);
    setError(null);
    try {
      const [next, learnerStates, learnerRecommendations] = await Promise.all([
        api.next(selected.id),
        api.state(selected.id),
        api.recommendations(selected.id),
      ]);
      setSelection(next);
      setStates(learnerStates);
      setRecommendations(learnerRecommendations);
      try {
        setResource(await api.resources());
      } catch {
        setResource(undefined);
      }
    } catch {
      setError("We couldn’t load this learner’s next lesson. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  const selectLearner = useCallback(
    async (selected: Learner) => {
      setLearner(selected);
      await loadWorkspace(selected);
    },
    [loadWorkspace],
  );

  const createLearner = useCallback(
    async (name: string, grade: number) => {
      setError(null);
      const created = await api.createLearner(name, grade);
      setLearners((current) => [created, ...current]);
      await selectLearner(created);
    },
    [selectLearner],
  );

  const refresh = useCallback(async () => {
    if (learner) await loadWorkspace(learner);
    setPending(await queuedCount());
  }, [learner, loadWorkspace]);

  const loadActivity = useCallback(
    async (activityId: string) => {
      if (online) {
        try {
          const payload = await api.activity(activityId);
          await cacheActivityContent(payload);
          return { payload, source: "network" as const };
        } catch (networkError) {
          const cached = await cachedActivityContent(activityId);
          if (cached) return { payload: cached, source: "cache" as const };
          throw networkError;
        }
      }
      const cached = await cachedActivityContent(activityId);
      if (!cached) throw new Error("This recommended activity has not been saved offline yet.");
      return { payload: cached, source: "cache" as const };
    },
    [online],
  );

  const submitAnswer = useCallback(
    async (answer: string, hints: number, responseTimeMs: number) => {
      if (!learner || !selection) return null;
      const cached = await cachedContentMetadata();
      const payload = {
        learner_id: learner.id,
        question_id: selection.question.id,
        submitted_answer: answer,
        response_time_ms: Math.max(0, Math.round(responseTimeMs)),
        hints_used: hints,
        offline: !online,
        offline_content: {
          cached_activity_ids: cached.activityIds,
          cached_concept_ids: cached.conceptIds,
          app_shell_available: Boolean(navigator.serviceWorker?.controller),
        },
      };
      if (!online) {
        await queueInteraction(payload);
        setPending(await queuedCount());
        return null;
      }
      const result = await api.submit(payload);
      await loadWorkspace(learner);
      return result;
    },
    [learner, loadWorkspace, online, selection],
  );

  useEffect(() => {
    void loadLearners();
    void queuedCount().then(setPending);
  }, [loadLearners]);

  useEffect(() => {
    const handleOnline = () => {
      setOnline(true);
      setSyncError(null);
      void flushQueue(api.submit)
        .then(async () => {
          setPending(await queuedCount());
          if (learner) await loadWorkspace(learner);
        })
        .catch(() => setSyncError("Pending work could not sync yet. We’ll try again later."));
    };
    const handleOffline = () => setOnline(false);
    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);
    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, [learner, loadWorkspace]);

  const value = useMemo<LearningContextValue>(
    () => ({
      learners,
      learner,
      states,
      selection,
      recommendations,
      resource,
      online,
      pending,
      loading,
      error,
      syncError,
      loadLearners,
      selectLearner,
      createLearner,
      refresh,
      loadActivity,
      submitAnswer,
    }),
    [
      createLearner,
      error,
      learner,
      learners,
      loadActivity,
      loadLearners,
      loading,
      online,
      pending,
      recommendations,
      refresh,
      resource,
      selectLearner,
      selection,
      states,
      submitAnswer,
      syncError,
    ],
  );
  return <LearningContext.Provider value={value}>{children}</LearningContext.Provider>;
}

export function useLearning(): LearningContextValue {
  const value = useContext(LearningContext);
  if (!value) throw new Error("useLearning must be used inside LearningProvider");
  return value;
}
