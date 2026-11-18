import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.job import Job
from backend.app.models.resume import Resume
from backend.app.models.match import JobMatch
from backend.app.models.profile import JobPreference
from backend.app.models.audit import AuditLog
from backend.app.schemas.match import MatchEvaluationRequest, MatchResponse
from backend.app.services.matching_engine import MatchingEngineService
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.post("/evaluate", response_model=MatchResponse)
def evaluate_job_match(
    req: MatchEvaluationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run explainable matching between user's resume and a job listing."""
    job = db.query(Job).filter(Job.id == req.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    # Pick specified resume or master resume
    if req.resume_id:
        resume = db.query(Resume).filter(Resume.id == req.resume_id, Resume.user_id == current_user.id).first()
    else:
        resume = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_master == True).first()
        if not resume:
            resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()

    if not resume:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No resume found. Please upload a CV first."
        )

    preferences = db.query(JobPreference).filter(JobPreference.user_id == current_user.id).first()

    eval_result = MatchingEngineService.evaluate_fit(resume, job, preferences)

    # Check if a match record already exists for this user and job
    match_record = db.query(JobMatch).filter(
        JobMatch.user_id == current_user.id,
        JobMatch.job_id == job.id
    ).first()

    if not match_record:
        match_record = JobMatch(
            user_id=current_user.id,
            job_id=job.id,
            resume_id=resume.id
        )
        db.add(match_record)

    match_record.resume_id = resume.id
    match_record.overall_score = eval_result["overall_score"]
    match_record.semantic_score = eval_result["semantic_score"]
    match_record.skill_coverage_score = eval_result["skill_coverage_score"]
    match_record.experience_fit_score = eval_result["experience_fit_score"]
    match_record.matched_skills = eval_result["matched_skills"]
    match_record.missing_skills = eval_result["missing_skills"]
    match_record.explanation = eval_result["explanation"]

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="match.evaluated",
        resource_type="job_match",
        resource_id=str(match_record.id),
        details={"job_id": str(job.id), "overall_score": eval_result["overall_score"]}
    )
    db.add(audit)

    db.commit()
    db.refresh(match_record)
    return match_record


@router.get("/", response_model=List[MatchResponse])
def list_user_matches(
    min_score: float = Query(0.0, ge=0.0, le=100.0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all evaluated job matches for the current authenticated user."""
    matches = (
        db.query(JobMatch)
        .filter(JobMatch.user_id == current_user.id, JobMatch.overall_score >= min_score)
        .order_by(JobMatch.overall_score.desc())
        .all()
    )
    return matches


@router.get("/{match_id}", response_model=MatchResponse)
def get_match_detail(
    match_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    match_record = db.query(JobMatch).filter(
        JobMatch.id == match_id,
        JobMatch.user_id == current_user.id
    ).first()
    if not match_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match record not found")
    return match_record

