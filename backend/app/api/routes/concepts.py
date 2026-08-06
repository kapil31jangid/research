"""Seeded curriculum endpoints."""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum.graph import graph_as_json
from app.curriculum.loader import load_concepts
from app.database.session import get_db
from app.models.concept import Concept
from app.schemas.concept import ConceptRead

router = APIRouter(tags=["curriculum"])


def serialise(concept: Concept) -> dict[str, object]:
    return {
        **{column.name: getattr(concept, column.name) for column in Concept.__table__.columns},
        "prerequisite_ids": json.loads(concept.prerequisite_ids),
        "activity_ids": json.loads(concept.activity_ids),
        "misconception_ids": json.loads(concept.misconception_ids),
    }


@router.get("/concepts", response_model=list[ConceptRead])
async def list_concepts(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    return [
        serialise(concept)
        for concept in db.scalars(select(Concept).order_by(Concept.difficulty, Concept.name))
    ]


@router.get("/concepts/{concept_id}", response_model=ConceptRead)
async def get_concept(concept_id: str, db: Session = Depends(get_db)) -> dict[str, object]:
    concept = db.get(Concept, concept_id)
    if concept is None:
        raise HTTPException(status_code=404, detail="Concept not found")
    return serialise(concept)


@router.get("/curriculum/graph")
async def curriculum_graph() -> dict[str, object]:
    return graph_as_json(load_concepts())
