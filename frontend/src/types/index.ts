export type ConceptState = { concept_id: string; mastery_probability: number; retained_mastery: number; uncertainty: number; attempts: number; suspected_misconception?: string | null };
export type Learner = { id: string; name: string; age_group: string; grade: number };
export type Question = { id: string; concept_id: string; text: string; options: string[]; explanation: string };
export type Recommendation = {
  selected_activity_id: string;
  selected_concept_id: string;
  adaptation_path: string;
  requested_adaptation_path?: string;
  explanation: string[];
  score: number;
  fallback_used?: boolean;
  fallback_reason?: string | null;
  ml_model_available?: boolean;
  model_version?: string | null;
  predicted_correctness_probability?: number | null;
  matching_offline_activity_ids?: string[];
  measured_total_adaptive_latency_ms?: number;
};
export type Resource = { score: number; level: string; offline: boolean; cpu_percent: number; available_memory_mb: number };
