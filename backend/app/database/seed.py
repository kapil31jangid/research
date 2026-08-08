"""Create database tables and idempotently seed curriculum content."""

import json

from sqlalchemy.orm import Session

import app.models  # noqa: F401  # Register every SQLAlchemy model before create_all().
from app.curriculum.content_loader import validate_activity_content
from app.curriculum.graph import build_graph
from app.curriculum.loader import load_activities, load_concepts, load_questions
from app.curriculum.registry import load_curriculum_registry, validate_curriculum_registry
from app.database.base import Base
from app.database.compatibility import apply_sqlite_compatibility_migrations
from app.database.session import SessionLocal, engine
from app.misconceptions.rules import load_rules
from app.models.activity import LearningActivity
from app.models.concept import Concept
from app.models.curriculum import (
    CurriculumBoard,
    CurriculumBook,
    CurriculumChapter,
    CurriculumSubject,
)
from app.models.question import Question

VALID_ADAPTATION_PATHS = {
    "diagnostic_assessment",
    "misconception_remediation",
    "prerequisite_review",
    "spaced_review",
    "rule_based_recommendation",
    "bkt_based_recommendation",
    "lightweight_ml_recommendation",
    "cached_offline_recommendation",
}


def validate_seed_data() -> None:
    """Fail fast when legacy concept references and activity metadata diverge."""
    concepts = load_concepts()
    activities = load_activities()
    questions = load_questions()
    validate_curriculum_registry(concepts=concepts, activities=activities, questions=questions)
    concept_ids = {item["id"] for item in concepts}
    activity_ids = [item["id"] for item in activities]
    if len(activity_ids) != len(set(activity_ids)):
        raise ValueError("Duplicate learning activity IDs in seed data")
    activity_by_id = {item["id"]: item for item in activities}
    for concept in concepts:
        missing = set(concept["activity_ids"]) - activity_by_id.keys()
        if missing:
            raise ValueError(
                f"Concept {concept['id']} references missing activities: {sorted(missing)}"
            )
    for activity in activities:
        if activity["concept_id"] not in concept_ids:
            raise ValueError(f"Activity {activity['id']} references an unknown concept")
        if not activity.get("is_active", True) or activity.get("deprecated_at") is not None:
            raise ValueError(f"Seed activity {activity['id']} must be active and non-deprecated")
        unknown_paths = set(activity["adaptation_paths"]) - VALID_ADAPTATION_PATHS
        if unknown_paths:
            raise ValueError(
                f"Activity {activity['id']} has invalid paths: {sorted(unknown_paths)}"
            )
    for rule in load_rules():
        remediation = activity_by_id.get(rule.remediation_activity)
        if remediation is None:
            raise ValueError(
                f"Misconception rule {rule.id} references a missing remediation activity"
            )
        if "misconception_remediation" not in remediation["adaptation_paths"]:
            raise ValueError(f"Remediation activity {remediation['id']} lacks its remediation path")
    validate_activity_content(activities=activities, concepts=concepts)


def seed_database(db: Session) -> None:
    concepts = load_concepts()
    validate_seed_data()
    build_graph(concepts)
    registry = load_curriculum_registry()
    for item in registry.boards:
        record = db.get(CurriculumBoard, item.id)
        values = item.model_dump()
        if record is None:
            db.add(CurriculumBoard(**values))
        else:
            for field, value in values.items():
                setattr(record, field, value)
    db.flush()
    for item in registry.subjects:
        record = db.get(CurriculumSubject, item.id)
        values = item.model_dump()
        if record is None:
            db.add(CurriculumSubject(**values))
        else:
            for field, value in values.items():
                setattr(record, field, value)
    db.flush()
    for item in registry.books:
        record = db.get(CurriculumBook, item.id)
        values = item.model_dump(mode="json")
        if record is None:
            db.add(CurriculumBook(**values))
        else:
            for field, value in values.items():
                setattr(record, field, value)
    db.flush()
    for item in registry.chapters:
        record = db.get(CurriculumChapter, item.id)
        values = item.model_dump(exclude={"concept_ids"})
        if record is None:
            db.add(CurriculumChapter(**values))
        else:
            for field, value in values.items():
                setattr(record, field, value)
    db.flush()
    for item in concepts:
        serialised = {
            **item,
            "prerequisite_ids": json.dumps(item["prerequisite_ids"]),
            "activity_ids": json.dumps(item["activity_ids"]),
            "misconception_ids": json.dumps(item["misconception_ids"]),
        }
        persisted = db.get(Concept, item["id"])
        if persisted is None:
            db.add(Concept(**serialised))
        else:
            for field, value in serialised.items():
                if field != "id":
                    setattr(persisted, field, value)
    for item in load_questions():
        if db.get(Question, item["id"]) is None:
            db.add(
                Question(
                    **{
                        **item,
                        "options": json.dumps(item["options"]),
                        "misconception_patterns": json.dumps(item["misconception_patterns"]),
                    }
                )
            )
    for item in load_activities():
        persisted = db.get(LearningActivity, item["id"])
        serialised = {
            **item,
            "adaptation_paths": json.dumps(item["adaptation_paths"]),
            "misconception_ids": json.dumps(item["misconception_ids"]),
        }
        if persisted is None:
            db.add(LearningActivity(**serialised))
            continue
        # Versioned seed metadata is authoritative, but lifecycle fields may have
        # been changed deliberately to retire content without deleting history.
        for field, value in serialised.items():
            if field not in {"id", "is_active", "deprecated_at", "deprecation_reason"}:
                setattr(persisted, field, value)
    db.commit()


def initialise_database() -> None:
    """Create schema and seed it. Safe to call on every local startup."""
    Base.metadata.create_all(bind=engine)
    apply_sqlite_compatibility_migrations(engine)
    with SessionLocal() as db:
        seed_database(db)


if __name__ == "__main__":
    initialise_database()
