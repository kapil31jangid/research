"""Learner-safe learning activity content endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.curriculum.content_loader import load_activity_content, load_content_for_concept
from app.curriculum.registry import get_curriculum_context
from app.database.session import get_db
from app.models.activity import LearningActivity
from app.schemas.activity_content import ActivityContent, ActivityContentRead, ActivitySummaryRead

router = APIRouter(tags=["activities"])


def _summary(activity: LearningActivity, content: ActivityContent) -> ActivitySummaryRead:
    return ActivitySummaryRead(
        id=activity.id,
        concept_id=activity.concept_id,
        title=activity.title,
        activity_type=activity.activity_type,
        difficulty=float(activity.difficulty),
        available_offline=activity.available_offline,
        estimated_minutes=content.estimated_minutes,
        curriculum_context=get_curriculum_context(activity.concept_id).model_dump(),
    )


@router.get("/activities/{activity_id}", response_model=ActivityContentRead)
async def get_activity_content(
    activity_id: str, db: Session = Depends(get_db)
) -> ActivityContentRead:
    activity = db.get(LearningActivity, activity_id)
    content = load_activity_content(activity_id)
    if activity is None or content is None or not activity.is_active or activity.deprecated_at:
        raise HTTPException(status_code=404, detail="Learning activity content not found")
    return ActivityContentRead(activity=_summary(activity, content), content=content)


@router.get("/concepts/{concept_id}/activities", response_model=list[ActivityContentRead])
async def list_concept_activity_content(
    concept_id: str, db: Session = Depends(get_db)
) -> list[ActivityContentRead]:
    content_by_id = {item.id: item for item in load_content_for_concept(concept_id)}
    activities = db.scalars(
        select(LearningActivity)
        .where(
            LearningActivity.concept_id == concept_id,
            LearningActivity.is_active.is_(True),
            LearningActivity.deprecated_at.is_(None),
        )
        .order_by(LearningActivity.id)
    )
    return [
        ActivityContentRead(
            activity=_summary(item, content_by_id[item.id]),
            content=content_by_id[item.id],
        )
        for item in activities
        if item.id in content_by_id
    ]
