from datetime import UTC, datetime, timedelta

from app.models.activity import LearningActivity
from app.models.concept import Concept
from app.models.learner_state import LearnerConceptState
from app.recommendation.candidate_generator import ActivityCandidate
from app.recommendation.ml_features import build_candidate_prediction_features


def test_candidate_features_use_real_activity_and_learner_values() -> None:
    now = datetime(2026, 1, 3, tzinfo=UTC)
    state = LearnerConceptState(
        learner_id="learner",
        concept_id="fractions",
        mastery_probability=0.8,
        uncertainty=0.2,
        recent_correctness="[true, false, true]",
        attempts=3,
        correct_attempts=2,
        forgetting_rate=0.2,
        last_practised_at=now - timedelta(days=2),
    )
    candidate = ActivityCandidate(
        "fractions", "activity", 0.2, 1.0, 0.2, 0.2, 0.0, 0.1, difficulty=4.0
    )
    activity = LearningActivity(
        id="activity",
        concept_id="fractions",
        title="A",
        description="",
        activity_type="practice_quiz",
        difficulty=4,
        adaptation_paths='["lightweight_ml_recommendation"]',
        misconception_ids="[]",
    )
    concept = Concept(
        id="fractions",
        name="Fractions",
        description="",
        difficulty=2,
        activity_ids='["activity"]',
    )
    features = build_candidate_prediction_features(
        candidate=candidate,
        activity=activity,
        concept=concept,
        learner_state=state,
        prerequisite_mastery=0.6,
        resource_score=0.9,
        now=now,
    )
    assert features.question_difficulty == 4.0
    assert features.concept_difficulty == 2.0
    assert features.recent_correctness == 2 / 3
    assert features.days_since_practice == 2.0
    assert features.retained_mastery < features.mastery
    assert features.prerequisite_mastery == 0.6
