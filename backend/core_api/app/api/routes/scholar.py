"""Ask-a-Scholar endpoints (v1.1 feature, routes ready)."""
from fastapi import APIRouter, Depends, HTTPException, Upload, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from uuid import UUID

from app.core.deps import get_db, get_current_user
from app.models.user import User, ScholarQuestion
from app.schemas.user import ScholarQuestionResponse

router = APIRouter()


@router.post("/scholar/questions", response_model=ScholarQuestionResponse)
async def create_scholar_question(
    text_body: Optional[str] = Form(None),
    topic: Optional[str] = Form(None),
    audio: Optional[Upload] = File(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit a question to the scholar board (audio note or text)."""
    audio_url = None
    if audio:
        # TODO: upload to S3, get URL
        audio_url = f"s3://qari-media/scholar-questions/{user.user_id}/{UUID(int=0)}"

    question = ScholarQuestion(
        user_id=user.user_id,
        text_body=text_body,
        audio_url=audio_url,
        status="queued",
    )
    db.add(question)
    await db.commit()
    return ScholarQuestionResponse.model_validate(question)


@router.get("/scholar/questions", response_model=list[ScholarQuestionResponse])
async def list_scholar_questions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List user's scholar questions with answered/pending states."""
    result = await db.execute(
        select(ScholarQuestion)
        .where(ScholarQuestion.user_id == user.user_id)
        .order_by(ScholarQuestion.created_at.desc())
    )
    return [ScholarQuestionResponse.model_validate(q) for q in result.scalars().all()]
