import { useEffect, useState } from "react";

import { Badge, Card, EmptyState, LoadingState, ProgressBar } from "../components/common/UI";
import { useLearning } from "../contexts/LearningContext";
import type { ActivityContentResponse } from "../types";
import { greeting, humanize, percent } from "../utils/format";

export function Dashboard({ onLearn }: { onLearn: () => void }) {
  const { learner, states, recommendations, resource, loading, loadActivity } = useLearning();
  const [activity, setActivity] = useState<ActivityContentResponse>();
  const recommendation = recommendations[0];

  useEffect(() => {
    if (!recommendation) {
      setActivity(undefined);
      return;
    }
    void loadActivity(recommendation.selected_activity_id)
      .then(({ payload }) => setActivity(payload))
      .catch(() => setActivity(undefined));
  }, [loadActivity, recommendation]);

  if (loading) return <LoadingState label="Loading dashboard" />;
  if (!learner) return null;
  const overall = states.length
    ? states.reduce((sum, state) => sum + state.mastery_probability, 0) / states.length
    : 0;
  const mastered = states.filter((state) => state.mastery_probability >= 0.8).length;
  const needsReview = states.filter((state) => state.mastery_probability < 0.6).length;
  const attempts = states.reduce((sum, state) => sum + state.attempts, 0);
  const recommendedMastery = states.find(
    (state) => state.concept_id === recommendation?.selected_concept_id,
  )?.mastery_probability ?? 0;

  return (
    <div className="page-stack">
      <header className="page-heading">
        <div>
          <p className="eyebrow">Your learning home</p>
          <h1>{greeting()}, {learner.name}</h1>
          <p>Here’s what RAPID-Learn recommends next.</p>
        </div>
      </header>

      {recommendation ? (
        <Card className="continue-card">
          <div className="continue-copy">
            <div className="flex flex-wrap gap-2">
              <Badge>{humanize(recommendation.adaptation_path)}</Badge>
              {activity?.content.estimated_minutes && (
                <Badge tone="slate">{activity.content.estimated_minutes} min</Badge>
              )}
            </div>
            <p className="eyebrow mt-6">Continue learning</p>
            <h2>{activity?.content.title ?? humanize(recommendation.selected_activity_id)}</h2>
            <p>{activity?.content.learning_objective ?? recommendation.explanation[0]}</p>
            <div className="mastery-inline">
              <span>Concept mastery</span><strong>{percent(recommendedMastery)}</strong>
            </div>
            <ProgressBar value={recommendedMastery} label="Recommended concept mastery" />
            <div className="recommended-because">
              <strong>Why this lesson?</strong><p>{recommendation.explanation[0]}</p>
            </div>
            <button className="button-primary" onClick={onLearn}>
              Continue learning <span aria-hidden="true">→</span>
            </button>
          </div>
          <div className="continue-visual" aria-hidden="true">
            <span>⅓</span><span>+</span><span>¼</span>
          </div>
        </Card>
      ) : (
        <EmptyState
          title="Start with a quick diagnostic"
          body="A short question helps RAPID-Learn choose the right first lesson."
          action={<button className="button-primary" onClick={onLearn}>Start diagnostic</button>}
        />
      )}

      <section>
        <div className="section-heading">
          <div><p className="eyebrow">At a glance</p><h2>Learning overview</h2></div>
          <span>{resource ? `${humanize(resource.level)} resources` : "Resource check unavailable"}</span>
        </div>
        <div className="stats-grid">
          <Stat label="Overall mastery" value={percent(overall)} detail="Across 12 fraction concepts" />
          <Stat label="Concepts mastered" value={`${mastered}`} detail="Mastery at or above 80%" />
          <Stat label="Needs practice" value={`${needsReview}`} detail="Concepts below 60%" />
          <Stat label="Recent evidence" value={`${attempts}`} detail="Questions completed" />
        </div>
      </section>

      <section>
        <div className="section-heading">
          <div><p className="eyebrow">Your pathway</p><h2>Concept progress</h2></div>
        </div>
        <div className="concept-grid">
          {states.slice(0, 6).map((state) => (
            <Card key={state.concept_id} className="concept-card">
              <div><h3>{humanize(state.concept_id)}</h3><strong>{percent(state.mastery_probability)}</strong></div>
              <ProgressBar value={state.mastery_probability} label={`${humanize(state.concept_id)} mastery`} />
              <small>{state.mastery_probability >= 0.8 ? "Mastered" : state.mastery_probability >= 0.6 ? "Developing" : "Needs practice"}</small>
            </Card>
          ))}
        </div>
      </section>
    </div>
  );
}

function Stat({ label, value, detail }: { label: string; value: string; detail: string }) {
  return <Card className="stat-card"><span>{label}</span><strong>{value}</strong><small>{detail}</small></Card>;
}
