import type {
  ActivityContentResponse,
  Book,
  Chapter,
  ClassOption,
  ConceptState,
  CurriculumBoard,
  CurriculumConcept,
  InteractionCreate,
  InteractionResponse,
  Learner,
  LearningSelection,
  Recommendation,
  Resource,
  Subject,
} from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
  ) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const message = await response.text();
    throw new ApiError(message || "Request failed", response.status);
  }
  return response.json() as Promise<T>;
}

export const api = {
  learners: () => request<Learner[]>("/learners"),
  createLearner: (name: string, classLevel: number, subjectId: string) =>
    request<Learner>("/learners", {
      method: "POST",
      body: JSON.stringify({
        name,
        age_group: classLevel <= 5 ? "9-11" : "10-12",
        grade: classLevel,
        class_level: classLevel,
        board_id: "ncert",
        active_subject_id: subjectId,
      }),
    }),
  updatePathway: (id: string, classLevel: number, subjectId: string, chapterId?: string) =>
    request<Learner>(`/learners/${encodeURIComponent(id)}/pathway`, {
      method: "PATCH",
      body: JSON.stringify({
        board_id: "ncert",
        class_level: classLevel,
        subject_id: subjectId,
        chapter_id: chapterId,
      }),
    }),
  boards: () => request<CurriculumBoard[]>("/curriculum/boards"),
  classes: (boardId = "ncert") =>
    request<ClassOption[]>(`/curriculum/boards/${encodeURIComponent(boardId)}/classes`),
  subjects: (classLevel: number, boardId = "ncert") =>
    request<Subject[]>(
      `/curriculum/boards/${encodeURIComponent(boardId)}/classes/${classLevel}/subjects`,
    ),
  books: (subjectId: string) =>
    request<Book[]>(`/curriculum/subjects/${encodeURIComponent(subjectId)}/books`),
  chapters: (bookId: string) =>
    request<Chapter[]>(`/curriculum/books/${encodeURIComponent(bookId)}/chapters`),
  concepts: () => request<CurriculumConcept[]>("/concepts"),
  state: (id: string) => request<ConceptState[]>(`/learners/${id}/state`),
  next: (id: string) =>
    request<LearningSelection>(`/questions/next?learner_id=${encodeURIComponent(id)}`),
  resources: () => request<Resource>("/resources/current"),
  recommendations: (id: string) =>
    request<Recommendation[]>(`/recommendations/${encodeURIComponent(id)}`),
  activity: (id: string) =>
    request<ActivityContentResponse>(`/activities/${encodeURIComponent(id)}`),
  submit: (payload: InteractionCreate) =>
    request<InteractionResponse>("/interactions", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
};
