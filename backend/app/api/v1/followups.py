import uuid
from typing import List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.application import Application, Followup
from backend.app.schemas.application import FollowupCreate, FollowupResponse
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=FollowupResponse, status_code=status.HTTP_201_CREATED)
def create_followup(
    followup_in: FollowupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule a follow-up reminder for an application."""
    app_record = db.query(Application).filter(
        Application.id == followup_in.application_id,
        Application.user_id == current_user.id
    ).first()
    if not app_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    job_title = app_record.job.title if app_record.job else "the role"
    company_name = app_record.job.company.name if (app_record.job and app_record.job.company) else "your team"
    draft = followup_in.suggested_draft or (
        f"Hi {company_name} team,\n\n"
        f"I wanted to follow up on my recent application for the {job_title} position. "
        f"I remain very excited about the opportunity and would love to answer any questions you may have.\n\n"
        f"Best regards,\n{current_user.full_name or 'Candidate'}"
    )

    followup = Followup(
        user_id=current_user.id,
        application_id=app_record.id,
        reminder_date=followup_in.reminder_date,
        suggested_draft=draft,
        status="pending"
    )
    db.add(followup)
    db.commit()
    db.refresh(followup)
    return followup


@router.get("/", response_model=List[FollowupResponse])
def list_followups(
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    q = db.query(Followup).filter(Followup.user_id == current_user.id)
    if status_filter:
        q = q.filter(Followup.status == status_filter)
    return q.order_by(Followup.reminder_date.asc()).all()


@router.put("/{followup_id}/dismiss", response_model=FollowupResponse)
def dismiss_followup(
    followup_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    followup = db.query(Followup).filter(
        Followup.id == followup_id,
        Followup.user_id == current_user.id
    ).first()
    if not followup:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Followup not found")
    followup.status = "dismissed"
    db.commit()
    db.refresh(followup)
    return followup

