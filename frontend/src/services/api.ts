import type { Learner, ConceptState, Question, Recommendation, Resource } from "../types";
const BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
async function request<T>(path: string, init?: RequestInit): Promise<T> { const response = await fetch(`${BASE}${path}`, { headers: { "Content-Type": "application/json" }, ...init }); if (!response.ok) throw new Error(await response.text()); return response.json(); }
export const api = {
  learners: () => request<Learner[]>("/learners"), createLearner: (name: string) => request<Learner>("/learners", { method: "POST", body: JSON.stringify({ name, age_group: "10-12", grade: 5 }) }),
  state: (id: string) => request<ConceptState[]>(`/learners/${id}/state`), next: (id: string) => request<{question: Question}>(`/questions/next?learner_id=${id}`),
  resources: () => request<Resource>("/resources/current"), recommendations: (id: string) => request<Recommendation[]>(`/recommendations/${id}`),
  submit: (payload: unknown) => request<any>("/interactions", { method: "POST", body: JSON.stringify(payload) })
};
