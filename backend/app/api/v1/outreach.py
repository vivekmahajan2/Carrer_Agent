import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.job import Job
from backend.app.models.recruiter import Recruiter
from backend.app.models.resume import Resume
from backend.app.models.outreach import OutreachMessage
from backend.app.models.audit import AuditLog, AgentRun
from backend.app.schemas.outreach import (
    OutreachGenerateRequest,
    OutreachUpdateRequest,
    OutreachResponse,
)
from backend.app.agents.graph import agent_graph
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.post("/generate", response_model=OutreachResponse, status_code=status.HTTP_201_CREATED)
async def generate_outreach(
    req: OutreachGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute LangGraph multi-agent flow to draft grounded outreach waiting for human approval."""
    job = db.query(Job).filter(Job.id == req.job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    recruiter = None
    if req.recruiter_id:
        recruiter = db.query(Recruiter).filter(Recruiter.id == req.recruiter_id).first()

    # Get master CV
    resume = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_master == True).first()
    if not resume:
        resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()

    cv_skills = [s.skill_name for s in resume.skills] if resume else ["Software Engineering"]

    initial_state = {
        "user_id": str(current_user.id),
        "job_id": str(job.id),
        "resume_id": str(resume.id) if resume else None,
        "recruiter_id": str(recruiter.id) if recruiter else None,
        "channel": req.channel,
        "job_details": {
            "title": job.title,
            "company_name": job.company.name if job.company else "the company",
            "required_skills": job.required_skills
        },
        "candidate_profile": {
            "full_name": current_user.full_name or "Candidate",
            "skills": cv_skills
        },
        "match_score": {},
        "recruiter_details": {
            "full_name": recruiter.full_name if recruiter else None,
            "title": recruiter.title if recruiter else None
        },
        "generated_subject": None,
        "generated_body": None,
        "cv_citations": [],
        "approval_status": "pending_approval",
        "outreach_id": None,
        "step_history": [],
        "error": None
    }

    # Run LangGraph workflow
    result = await agent_graph.ainvoke(initial_state)

    # Persist draft in DB with status "pending_approval"
    outreach = OutreachMessage(
        user_id=current_user.id,
        job_id=job.id,
        recruiter_id=recruiter.id if recruiter else None,
        channel=req.channel,
        subject=result.get("generated_subject"),
        body_text=result.get("generated_body") or "Tailored outreach draft.",
        cv_grounding_citations=result.get("cv_citations") or [],
        status="pending_approval"
    )
    db.add(outreach)
    db.flush()

    # Track AgentRun
    agent_run = AgentRun(
        user_id=current_user.id,
        thread_id=f"run-{uuid.uuid4()}",
        workflow_type="outreach_generation",
        status="waiting_approval",
        current_node="human_approval_checkpoint",
        state_payload={"outreach_id": str(outreach.id), "steps": result.get("step_history", [])}
    )
    db.add(agent_run)

    audit = AuditLog(
        user_id=current_user.id,
        action="outreach.generated_draft",
        resource_type="outreach_message",
        resource_id=str(outreach.id),
        details={"channel": req.channel, "job_id": str(job.id)}
    )
    db.add(audit)

    db.commit()
    db.refresh(outreach)
    return outreach


@router.get("/", response_model=List[OutreachResponse])
def list_outreach_messages(
    status_filter: Optional[str] = Query(None, description="pending_approval, approved, rejected, sent"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List outreach messages for the tenant."""
    q = db.query(OutreachMessage).filter(OutreachMessage.user_id == current_user.id)
    if status_filter:
        q = q.filter(OutreachMessage.status == status_filter)
    return q.order_by(OutreachMessage.created_at.desc()).all()


@router.get("/{outreach_id}", response_model=OutreachResponse)
def get_outreach_message(
    outreach_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    msg = db.query(OutreachMessage).filter(
        OutreachMessage.id == outreach_id,
        OutreachMessage.user_id == current_user.id
    ).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach message not found")
    return msg


@router.put("/{outreach_id}", response_model=OutreachResponse)
def update_outreach_draft(
    outreach_id: uuid.UUID,
    req: OutreachUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Edit message draft before approving."""
    msg = db.query(OutreachMessage).filter(
        OutreachMessage.id == outreach_id,
        OutreachMessage.user_id == current_user.id
    ).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Outreach message not found")

    if req.subject is not None:
        msg.subject = req.subject
    msg.body_text = req.body_text

    db.commit()
    db.refresh(msg)
    return msg

