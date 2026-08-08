import { useEffect, useState } from "react";

import { Badge, ErrorState, LoadingState } from "../components/common/UI";
import { ActivityRenderer } from "../components/learning/ActivityRenderer";
import { QuizCard } from "../components/learning/QuizCard";
import { useLearning } from "../contexts/LearningContext";
import type { ActivityContentResponse, InteractionResponse } from "../types";
import { humanize } from "../utils/format";

type Stage = "lesson" | "check" | "feedback";
type SubmissionOutcome =
  | { type: "processed"; result: InteractionResponse }
  | { type: "queued" };

export function Learn({ onReturnDashboard }: { onReturnDashboard: () => void }) {
  const { recommendations, selection, loadActivity, submitAnswer, online } = useLearning();
  const recommendation = recommendations[0];
  const [content, setContent] = useState<ActivityContentResponse>();
  const [source, setSource] = useState<"network" | "cache">("network");
  const [stage, setStage] = useState<Stage>(recommendation ? "lesson" : "check");
  const [loading, setLoading] = useState(Boolean(recommendation));
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [feedback, setFeedback] = useState<SubmissionOutcome | null>(null);
  const load = async () => {
    if (!recommendation) { setLoading(false); setStage("check"); return; }
    setLoading(true); setError(null);
    try { const result = await loadActivity(recommendation.selected_activity_id); setContent(result.payload); setSource(result.source); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "This lesson could not be loaded."); }
    finally { setLoading(false); }
  };
  useEffect(() => { void load(); }, [recommendation?.selected_activity_id, loadActivity]);
  async function submit(answer: string, hints: number, elapsedMs: number) { setSubmitting(true); setError(null); try { const result = await submitAnswer(answer, hints, elapsedMs); setFeedback(result ? { type: "processed", result } : { type: "queued" }); setStage("feedback"); } catch { setError("Your answer could not be submitted. Please try again."); } finally { setSubmitting(false); } }
  if (loading) return <LoadingState label="Loading your lesson" />;
  if (error && stage !== "check") return <ErrorState message={error} onRetry={() => void load()} secondaryAction={<button className="text-button" onClick={() => setStage("check")}>Continue to the quick check</button>} />;
  if (!selection) return <ErrorState message="No eligible learning question is available." onRetry={() => window.location.reload()} />;
  if (stage === "feedback") return <Feedback outcome={feedback} online={online} canReviewLesson={Boolean(content)} onReturnDashboard={onReturnDashboard} onReviewLesson={() => { setFeedback(null); setStage("lesson"); }} onContinue={() => { setFeedback(null); setStage(recommendations[0] ? "lesson" : "check"); }} />;
  if (stage === "check") return <div className="learning-stage"><div className="learn-topline"><Badge tone="cyan">Adaptive checkpoint</Badge><span>{humanize(selection.selection_type)}</span></div>{error && <div className="inline-error" role="alert">{error}</div>}<QuizCard question={selection.question} onSubmit={(answer, hints, elapsed) => void submit(answer, hints, elapsed)} submitting={submitting} /></div>;
  if (!content) return <ErrorState message="No recommendation content is available yet." onRetry={() => setStage("check")} />;
  return <div className="learning-stage"><div className="learn-topline"><div><Badge tone={recommendation?.adaptation_path === "misconception_remediation" ? "amber" : "indigo"}>{recommendation ? humanize(recommendation.adaptation_path) : "Guided lesson"}</Badge>{source === "cache" && <Badge tone="slate">Saved offline</Badge>}</div><span>{content.content.estimated_minutes ?? 5} min</span></div>{recommendation?.adaptation_path === "misconception_remediation" && <div className="supportive-banner"><strong>Let’s fix one common mix-up</strong><p>This short visual is here to make the idea clearer—not to mark a mistake.</p></div>}<ActivityRenderer content={content.content} /><div className="lesson-footer"><div><strong>Ready to try it?</strong><p>A quick check helps choose your next best activity.</p></div><button className="button-primary" onClick={() => setStage("check")}>Start quick check</button></div></div>;
}

function Feedback({ outcome, online, canReviewLesson, onReturnDashboard, onReviewLesson, onContinue }: { outcome: SubmissionOutcome | null; online: boolean; canReviewLesson: boolean; onReturnDashboard: () => void; onReviewLesson: () => void; onContinue: () => void }) {
  if (outcome?.type === "queued") return <section className="feedback-card queued" role="status"><span className="feedback-icon">↻</span><p className="eyebrow">Saved on this device · Pending sync</p><h1>Your answer will sync when you’re back online</h1><p>RAPID-Learn needs that sync before it can calculate your next adaptive pathway.</p><div className="queued-actions"><button className="button-primary" onClick={onReturnDashboard}>Return to dashboard</button>{canReviewLesson && <button className="button-secondary" onClick={onReviewLesson}>Review saved lesson</button>}</div></section>;
  const result = outcome?.type === "processed" ? outcome.result : null;
  const correct = Boolean(result?.interaction_result.correct);
  return <section className={`feedback-card ${correct ? "correct" : "review"}`}><span className="feedback-icon">{correct ? "✓" : "↗"}</span><p className="eyebrow">{correct ? "Correct" : "Not quite yet"}</p><h1>{correct ? "Nice reasoning." : "Let’s strengthen this idea."}</h1><p>{result?.explanation[0] ?? (online ? "Your next activity is ready." : "Your answer is saved.")}</p>{result && <div className="next-path"><span>Next adaptive path</span><strong>{humanize(result.decision.adaptation_path)}</strong></div>}<button className="button-primary" onClick={onContinue}>Continue learning</button></section>;
}
