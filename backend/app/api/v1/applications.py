import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.job import Job
from backend.app.models.application import Application
from backend.app.models.audit import AuditLog
from backend.app.schemas.application import (
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationResponse
)
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.post("/", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def create_application(
    app_in: ApplicationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a job to Application CRM."""
    job = db.query(Job).filter(Job.id == app_in.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    existing = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_id == app_in.job_id
    ).first()
    if existing:
        return existing

    app_record = Application(
        user_id=current_user.id,
        job_id=app_in.job_id,
        status=app_in.status,
        notes=app_in.notes,
        application_url=app_in.application_url or job.source_url,
        history=[{
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": app_in.status,
            "note": "Created in Application CRM"
        }]
    )
    db.add(app_record)
    db.commit()
    db.refresh(app_record)
    return app_record


@router.get("/", response_model=List[ApplicationResponse])
def list_applications(
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List tracked applications for the user."""
    q = db.query(Application).filter(Application.user_id == current_user.id)
    if status_filter:
        q = q.filter(Application.status == status_filter)
    return q.order_by(Application.created_at.desc()).all()


@router.put("/{application_id}", response_model=ApplicationResponse)
def update_application(
    application_id: uuid.UUID,
    app_update: ApplicationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app_record = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    if not app_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")

    if app_update.status:
        old_status = app_record.status
        app_record.status = app_update.status
        history = list(app_record.history or [])
        history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": app_update.status,
            "note": f"Status changed from {old_status} to {app_update.status}"
        })
        app_record.history = history

    if app_update.notes is not None:
        app_record.notes = app_update.notes
    if app_update.applied_at:
        app_record.applied_at = app_update.applied_at

    db.commit()
    db.refresh(app_record)
    return app_record


@router.delete("/{application_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_application(
    application_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    app_record = db.query(Application).filter(
        Application.id == application_id,
        Application.user_id == current_user.id
    ).first()
    if not app_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    db.delete(app_record)
    db.commit()
    return None

