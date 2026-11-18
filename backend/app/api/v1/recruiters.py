import uuid
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.core.database import get_db
from backend.app.models.recruiter import Recruiter, RecruiterEvidence
from backend.app.models.company import Company
from backend.app.models.user import User
from backend.app.api.deps import get_current_user

router = APIRouter()


class RecruiterEvidenceResponse(BaseModel):
    id: uuid.UUID
    evidence_type: str
    public_source_url: str
    snippet: Optional[str] = None


class RecruiterResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: Optional[str] = None
    full_name: str
    title: Optional[str] = None
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    is_verified_public: bool
    evidence: List[RecruiterEvidenceResponse] = []


@router.get("/", response_model=List[RecruiterResponse])
def get_recruiters(
    company_id: Optional[uuid.UUID] = Query(None),
    query: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve verified public recruiters, founders, and hiring managers with evidence provenance."""
    q = db.query(Recruiter).join(Company)
    if company_id:
        q = q.filter(Recruiter.company_id == company_id)
    if query:
        q = q.filter(Recruiter.full_name.ilike(f"%{query}%") | Recruiter.title.ilike(f"%{query}%"))

    recruiters = q.order_by(Recruiter.created_at.desc()).offset(skip).limit(limit).all()

    response = []
    for r in recruiters:
        evidence_list = [
            RecruiterEvidenceResponse(
                id=ev.id,
                evidence_type=ev.evidence_type,
                public_source_url=ev.public_source_url,
                snippet=ev.snippet
            ) for ev in r.evidence
        ]
        response.append(
            RecruiterResponse(
                id=r.id,
                company_id=r.company_id,
                company_name=r.company.name if r.company else "Unknown",
                full_name=r.full_name,
                title=r.title,
                linkedin_url=r.linkedin_url,
                email=r.email,
                is_verified_public=r.is_verified_public,
                evidence=evidence_list
            )
        )
    return response


@router.get("/{recruiter_id}", response_model=RecruiterResponse)
def get_recruiter(
    recruiter_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    r = db.query(Recruiter).filter(Recruiter.id == recruiter_id).first()
    if not r:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recruiter not found")

    evidence_list = [
        RecruiterEvidenceResponse(
            id=ev.id,
            evidence_type=ev.evidence_type,
            public_source_url=ev.public_source_url,
            snippet=ev.snippet
        ) for ev in r.evidence
    ]
    return RecruiterResponse(
        id=r.id,
        company_id=r.company_id,
        company_name=r.company.name if r.company else "Unknown",
        full_name=r.full_name,
        title=r.title,
        linkedin_url=r.linkedin_url,
        email=r.email,
        is_verified_public=r.is_verified_public,
        evidence=evidence_list
    )

