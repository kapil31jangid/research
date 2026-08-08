import type {
  ActivityContentResponse,
  ConceptState,
  InteractionCreate,
  InteractionResponse,
  Learner,
  LearningSelection,
  Recommendation,
  Resource,
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
  createLearner: (name: string, grade: number) =>
    request<Learner>("/learners", {
      method: "POST",
      body: JSON.stringify({ name, age_group: grade <= 5 ? "9-11" : "10-12", grade }),
    }),
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
