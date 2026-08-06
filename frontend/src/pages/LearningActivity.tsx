import type { Recommendation } from "../types";

export function LearningActivity({ recommendation }: { recommendation?: Recommendation }) {
  if (!recommendation) return <p>Complete a quick check to receive an activity.</p>;
  return <section><h2>Learning activity</h2><article className="rounded border p-4"><b>{recommendation.selected_activity_id.replaceAll("_", " ")}</b><p className="mt-2">Work through the visual or worked example step by step. Explain why the denominator represents equal-sized parts before continuing.</p><p className="mt-2 text-sm text-slate-600">Adaptation pathway: {recommendation.adaptation_path}</p></article></section>;
}
