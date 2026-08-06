import type { Resource, Recommendation } from "../types";

export function ResearchDashboard({ resource, recs }: { resource?: Resource; recs: Recommendation[] }) {
  const latest = recs[0];
  return <section><h2>Research dashboard</h2><dl className="grid grid-cols-2 gap-3"><div><dt>Resource score</dt><dd>{resource?.score.toFixed(2) ?? "–"}</dd></div><div><dt>CPU</dt><dd>{resource?.cpu_percent.toFixed(1) ?? "–"}%</dd></div><div><dt>Recommendations</dt><dd>{recs.length}</dd></div><div><dt>Latest pathway</dt><dd>{latest?.adaptation_path ?? "–"}</dd></div><div><dt>Requested pathway</dt><dd>{latest?.requested_adaptation_path ?? "–"}</dd></div><div><dt>Model version</dt><dd>{latest?.model_version ?? "–"}</dd></div><div><dt>Offline reason</dt><dd>{latest?.offline_content_reason ?? "–"}</dd></div><div><dt>Adaptive latency</dt><dd>{latest?.measured_total_adaptive_latency_ms?.toFixed(2) ?? "–"} ms</dd></div></dl></section>;
}
