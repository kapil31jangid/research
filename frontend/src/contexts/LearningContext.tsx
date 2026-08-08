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
  Book,
  Chapter,
  ClassOption,
  ConceptState,
  CurriculumBoard,
  CurriculumConcept,
  CurriculumContext,
  InteractionResponse,
  Learner,
  LearningSelection,
  Recommendation,
  Resource,
  Subject,
} from "../types";

type ContentSource = "network" | "cache";
type LearningContextValue = {
  learners: Learner[];
  learner?: Learner;
  states: ConceptState[];
  selection?: LearningSelection;
  recommendations: Recommendation[];
  resource?: Resource;
  boards: CurriculumBoard[];
  classes: ClassOption[];
  subjects: Subject[];
  books: Book[];
  chapters: Chapter[];
  concepts: CurriculumConcept[];
  curriculum?: CurriculumContext;
  online: boolean;
  pending: number;
  loading: boolean;
  error: string | null;
  syncError: string | null;
  loadLearners: () => Promise<void>;
  selectLearner: (learner: Learner) => Promise<void>;
  createLearner: (name: string, classLevel: number, subjectId: string) => Promise<void>;
  switchPathway: (classLevel: number, subjectId: string, chapterId?: string) => Promise<void>;
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
  const [boards, setBoards] = useState<CurriculumBoard[]>([]);
  const [classes, setClasses] = useState<ClassOption[]>([]);
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [books, setBooks] = useState<Book[]>([]);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [concepts, setConcepts] = useState<CurriculumConcept[]>([]);
  const [curriculum, setCurriculum] = useState<CurriculumContext>();
  const [online, setOnline] = useState(() => navigator.onLine);
  const [pending, setPending] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncError, setSyncError] = useState<string | null>(null);

  const loadLearners = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [profiles, boardItems, classItems] = await Promise.all([
        api.learners(),
        api.boards(),
        api.classes(),
      ]);
      const availableClasses = classItems.filter((item) => item.content_status === "available");
      const subjectGroups = await Promise.all(
        availableClasses.map((item) => api.subjects(item.class_level, item.board_id)),
      );
      setLearners(profiles);
      setBoards(boardItems);
      setClasses(classItems);
      setSubjects(subjectGroups.flat());
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
      const [next, learnerStates, learnerRecommendations, subjectItems, conceptItems] = await Promise.all([
        api.next(selected.id),
        api.state(selected.id),
        api.recommendations(selected.id),
        api.subjects(selected.class_level, selected.board_id),
        api.concepts(),
      ]);
      const activeSubject = subjectItems.find((item) => item.id === selected.active_subject_id);
      const bookItems = activeSubject ? await api.books(activeSubject.id) : [];
      const activeBook =
        bookItems.find((item) => item.id === selected.active_book_id) ?? bookItems[0];
      const chapterItems = activeBook ? await api.chapters(activeBook.id) : [];
      const activeChapter =
        chapterItems.find((item) => item.id === selected.active_chapter_id) ?? chapterItems[0];
      setSelection(next);
      setStates(learnerStates);
      setRecommendations(learnerRecommendations);
      setSubjects((current) => [
        ...current.filter((item) => !subjectItems.some((subject) => subject.id === item.id)),
        ...subjectItems,
      ]);
      setBooks(bookItems);
      setChapters(chapterItems);
      setConcepts(conceptItems);
      setCurriculum(
        activeSubject &&
          activeBook &&
          activeChapter &&
          activeSubject.curriculum_pack_id &&
          activeSubject.curriculum_pack_version
          ? {
              board_id: selected.board_id,
              board_name:
                boards.find((item) => item.id === selected.board_id)?.name ?? "NCERT",
              class_level: selected.class_level,
              subject_id: activeSubject.id,
              subject_name: activeSubject.name,
              book_id: activeBook.id,
              book_title: activeBook.title,
              chapter_id: activeChapter.id,
              chapter_title: activeChapter.title,
              concept_id: null,
              concept_name: null,
              curriculum_pack_id: activeSubject.curriculum_pack_id,
              curriculum_pack_version: activeSubject.curriculum_pack_version,
              content_origin: "original_adaptive_material",
            }
          : undefined,
      );
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
  }, [boards]);

  const selectLearner = useCallback(
    async (selected: Learner) => {
      setLearner(selected);
      await loadWorkspace(selected);
    },
    [loadWorkspace],
  );

  const createLearner = useCallback(
    async (name: string, classLevel: number, subjectId: string) => {
      setError(null);
      const created = await api.createLearner(name, classLevel, subjectId);
      setLearners((current) => [created, ...current]);
      await selectLearner(created);
    },
    [selectLearner],
  );

  const switchPathway = useCallback(
    async (classLevel: number, subjectId: string, chapterId?: string) => {
      if (!learner) return;
      setError(null);
      const updated = await api.updatePathway(learner.id, classLevel, subjectId, chapterId);
      setLearner(updated);
      setLearners((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      await loadWorkspace(updated);
    },
    [learner, loadWorkspace],
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
          const cached = await cachedActivityContent(activityId, curriculum);
          if (cached) return { payload: cached, source: "cache" as const };
          throw networkError;
        }
      }
      const cached = await cachedActivityContent(activityId, curriculum);
      if (!cached) throw new Error("This recommended activity has not been saved offline yet.");
      return { payload: cached, source: "cache" as const };
    },
    [curriculum, online],
  );

  const submitAnswer = useCallback(
    async (answer: string, hints: number, responseTimeMs: number) => {
      if (!learner || !selection || !curriculum) return null;
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
          cached_curriculum_keys: cached.curriculumKeys,
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
      if (!online) {
        await queueInteraction(payload);
        setPending(await queuedCount());
        return null;
      }
      const result = await api.submit(payload);
      await loadWorkspace(learner);
      return result;
    },
    [curriculum, learner, loadWorkspace, online, selection],
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
      boards,
      classes,
      subjects,
      books,
      chapters,
      concepts,
      curriculum,
      online,
      pending,
      loading,
      error,
      syncError,
      loadLearners,
      selectLearner,
      createLearner,
      switchPathway,
      refresh,
      loadActivity,
      submitAnswer,
    }),
    [
      boards,
      books,
      chapters,
      classes,
      concepts,
      createLearner,
      curriculum,
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
      subjects,
      switchPathway,
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
