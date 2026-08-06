"""Create database tables and idempotently seed curriculum content."""

import json

from sqlalchemy.orm import Session

import app.models  # noqa: F401  # Register every SQLAlchemy model before create_all().
from app.curriculum.graph import build_graph
from app.curriculum.loader import load_concepts, load_questions
from app.database.base import Base
from app.database.session import SessionLocal, engine
from app.models.concept import Concept
from app.models.question import Question


def seed_database(db: Session) -> None:
    concepts = load_concepts()
    build_graph(concepts)
    for item in concepts:
        if db.get(Concept, item["id"]) is None:
            db.add(
                Concept(
                    **{
                        **item,
                        "prerequisite_ids": json.dumps(item["prerequisite_ids"]),
                        "activity_ids": json.dumps(item["activity_ids"]),
                        "misconception_ids": json.dumps(item["misconception_ids"]),
                    }
                )
            )
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
    db.commit()


def initialise_database() -> None:
    """Create schema and seed it. Safe to call on every local startup."""
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_database(db)


if __name__ == "__main__":
    initialise_database()
