import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from backend.app.core.database import get_db
from backend.app.models.job import Job
from backend.app.models.company import Company
from backend.app.models.user import User
from backend.app.schemas.job import JobCreate, JobResponse, JobFilter
from backend.app.services.connectors.base import NormalizedJobData
from backend.app.services.job_service import JobIngestionService
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.get("/", response_model=List[JobResponse])
def get_jobs(
    query: Optional[str] = Query(None, description="Search keyword in title, description, company"),
    employment_type: Optional[str] = Query(None, description="full-time, internship"),
    is_remote: Optional[bool] = Query(None),
    location: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """Retrieve discovered and ingested job listings with filters."""
    q = db.query(Job).join(Company).filter(Job.is_active == True)

    if query:
        search_pattern = f"%{query}%"
        q = q.filter(
            or_(
                Job.title.ilike(search_pattern),
                Job.description.ilike(search_pattern),
                Company.name.ilike(search_pattern)
            )
        )
    if employment_type:
        q = q.filter(Job.employment_type == employment_type)
    if is_remote is not None:
        q = q.filter(Job.is_remote == is_remote)
    if location:
        q = q.filter(Job.location.ilike(f"%{location}%"))

    jobs = q.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()

    # Format company name in response
    response_list = []
    for j in jobs:
        resp = JobResponse.model_validate(j)
        resp.company_name = j.company.name if j.company else "Unknown"
        response_list.append(resp)
    return response_list


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """Get single job listing detail."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    resp = JobResponse.model_validate(job)
    resp.company_name = job.company.name if job.company else "Unknown"
    return resp


@router.post("/manual", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
def create_manual_job(
    job_in: JobCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually add a job listing or parse from user input."""
    norm_job = NormalizedJobData(
        title=job_in.title,
        company_name=job_in.company_name,
        company_website=job_in.company_website,
        company_industry=job_in.company_industry,
        description=job_in.description,
        requirements=job_in.requirements,
        required_skills=job_in.required_skills,
        employment_type=job_in.employment_type,
        location=job_in.location,
        is_remote=job_in.is_remote,
        remote_policy=job_in.remote_policy,
        salary_min=job_in.salary_min,
        salary_max=job_in.salary_max,
        salary_currency=job_in.salary_currency,
        source_platform=job_in.platform,
        source_url=job_in.source_url
    )
    job, is_new = JobIngestionService.ingest_job(db, norm_job)
    resp = JobResponse.model_validate(job)
    resp.company_name = job.company.name if job.company else job_in.company_name
    return resp


@router.post("/sync")
async def trigger_source_sync(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Trigger job ingestion across all configured connectors."""
    result = await JobIngestionService.sync_all_sources(db)
    return {
        "status": "success",
        "message": "Job discovery sync completed",
        "result": result
    }

