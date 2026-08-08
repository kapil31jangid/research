export type ConceptState = {
  concept_id: string;
  mastery_probability: number;
  retained_mastery: number;
  uncertainty: number;
  attempts: number;
  correct_attempts: number;
  recent_correctness: boolean[];
  average_response_time: number | null;
  response_time_variation: number;
  hint_usage_rate: number;
  last_practised_at: string | null;
  forgetting_rate: number;
  suspected_misconception: string | null;
  misconception_confidence: number;
};

export type Learner = {
  id: string;
  name: string;
  age_group: string;
  grade: number;
  preferred_language: string;
  device_profile: string;
  created_at: string;
  last_active_at: string;
  board_id: string;
  class_level: number;
  active_subject_id: string | null;
  active_book_id: string | null;
  active_chapter_id: string | null;
};

export type CurriculumBoard = {
  id: string;
  name: string;
  country: string | null;
  description: string | null;
};
export type ClassOption = {
  board_id: string;
  class_level: number;
  content_status: "available" | "partial" | "planned";
};
export type Subject = {
  id: string;
  board_id: string;
  class_level: number;
  name: string;
  slug: string;
  description: string;
  content_status: "available" | "partial" | "planned";
  is_active: boolean;
  curriculum_pack_id: string | null;
  curriculum_pack_version: string | null;
};
export type Book = {
  id: string;
  subject_id: string;
  title: string;
  source: string;
  language: string;
  official_reference_url: string | null;
  edition: string | null;
  is_active: boolean;
};
export type Chapter = {
  id: string;
  book_id: string;
  chapter_number: number;
  title: string;
  slug: string;
  description: string;
  sequence: number;
  concept_ids: string[];
  is_active: boolean;
};
export type CurriculumContext = {
  board_id: string;
  board_name: string;
  class_level: number;
  subject_id: string;
  subject_name: string;
  book_id: string;
  book_title: string;
  chapter_id: string;
  chapter_title: string;
  concept_id: string | null;
  concept_name: string | null;
  curriculum_pack_id: string;
  curriculum_pack_version: string;
  content_origin: "original_adaptive_material";
};
export type CurriculumConcept = {
  id: string;
  chapter_id: string;
  name: string;
  description: string;
  difficulty: number;
  mastery_threshold: number;
  prerequisite_ids: string[];
  activity_ids: string[];
  misconception_ids: string[];
};

export type Question = {
  id: string;
  concept_id: string;
  text: string;
  answer_type: string;
  options: string[];
  difficulty: number;
  explanation: string;
  diagnostic_value: number;
  estimated_cost_ms: number;
  misconception_patterns: string[];
  template_id: string | null;
};

export type LearningSelection = {
  learner_id: string;
  selection_type: string;
  concept_id: string;
  question: Question;
  rationale: string;
  prerequisite_mastery: number;
};

export type CandidatePrediction = { activity_id: string; probability: number };
export type Recommendation = {
  id: string;
  learner_id: string;
  selected_activity_id: string;
  selected_concept_id: string;
  adaptation_path: string;
  requested_adaptation_path: string;
  explanation: string[];
  score: number;
  expected_learning_gain: number;
  computational_cost_ms: number;
  fallback_used: boolean;
  fallback_reason: string | null;
  ml_model_available: boolean;
  model_version: string | null;
  predicted_correctness_probability: number | null;
  selected_candidate_predicted_probability: number | null;
  candidate_prediction_summary: CandidatePrediction[];
  matching_offline_activity_ids: string[];
  offline_content_reason: string | null;
  offline_content_available: boolean;
  triggered_rules: string[];
  rejected_paths: string[];
  measured_controller_latency_ms: number;
  measured_recommendation_latency_ms: number;
  measured_total_adaptive_latency_ms: number;
  controller_mode: string;
  created_at: string;
  curriculum_context: CurriculumContext;
};

export type Resource = {
  score: number;
  level: string;
  offline: boolean;
  network_available: boolean;
  network_quality: number | null;
  cpu_percent: number;
  available_memory_mb: number;
  total_memory_mb: number;
  battery_percent: number | null;
  battery_charging: boolean | null;
  storage_available_mb: number;
  inference_latency_ms: number;
};

export type ExplanationSection = { type: "explanation"; heading?: string; body: string };
export type WorkedExampleSection = {
  type: "worked_example";
  heading: string;
  problem: string;
  steps: string[];
  answer: string;
  reasoning?: string;
};
export type StepsSection = { type: "steps"; heading: string; steps: string[] };
export type CalloutSection = {
  type: "tip" | "warning" | "formula" | "reflection";
  heading?: string;
  body: string;
};
export type FractionVisualSection = {
  type: "visual_model" | "fraction_bar";
  heading?: string;
  numerator: number;
  denominator: number;
  comparison_numerator?: number;
  comparison_denominator?: number;
  caption: string;
};
export type NumberLineSection = {
  type: "number_line";
  heading?: string;
  denominator: number;
  points: number[];
  caption: string;
};
export type CheckpointSection = {
  type: "checkpoint" | "practice";
  heading: string;
  prompt: string;
  options: string[];
  hint?: string;
};
export type ActivitySection =
  | ExplanationSection
  | WorkedExampleSection
  | StepsSection
  | CalloutSection
  | FractionVisualSection
  | NumberLineSection
  | CheckpointSection;

export type ActivityContent = {
  id: string;
  concept_id: string;
  title: string;
  subtitle: string | null;
  content_type: string;
  estimated_minutes: number | null;
  learning_objective: string | null;
  sections: ActivitySection[];
  offline_ready: boolean;
  content_origin: "original_adaptive_material";
  aligned_board: string;
  official_reference_url: string | null;
};
export type ActivityContentResponse = {
  activity: {
    id: string;
    concept_id: string;
    title: string;
    activity_type: string;
    difficulty: number;
    available_offline: boolean;
    estimated_minutes: number | null;
    curriculum_context: CurriculumContext;
  };
  content: ActivityContent;
};

export type OfflineContentMetadata = {
  cached_activity_ids: string[];
  cached_concept_ids: string[];
  app_shell_available: boolean;
  cached_curriculum_keys: string[];
};
export type InteractionCreate = {
  learner_id: string;
  question_id: string;
  submitted_answer: string;
  response_time_ms: number;
  hints_used: number;
  offline: boolean;
  offline_content: OfflineContentMetadata;
  curriculum_context: {
    board_id: string;
    class_level: number;
    subject_id: string;
    book_id: string;
    chapter_id: string;
    curriculum_pack_version: string;
  };
};
export type InteractionResponse = {
  learner_id: string;
  interaction_result: {
    id: string;
    correct: boolean;
    concept_id: string;
    response_time_ms: number;
    curriculum_context: InteractionCreate["curriculum_context"];
  };
  learner_state: ConceptState;
  decision: Recommendation;
  explanation: string[];
};
