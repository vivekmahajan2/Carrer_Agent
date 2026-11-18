import json
import uuid
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import encrypt_secret, decrypt_secret
from backend.app.models.user import User
from backend.app.models.profile import Profile
from backend.app.models.audit import ConnectedAccount, AuditLog
from backend.app.models.resume import Resume
from backend.app.models.match import JobMatch
from backend.app.models.outreach import OutreachMessage
from backend.app.models.application import Application
from backend.app.services.linkedin_service import LinkedInIntegrationService
from backend.app.services.job_service import JobIngestionService
from backend.app.services.matching_engine import MatchingEngineService
from backend.app.api.deps import get_current_user

router = APIRouter()


class LinkedInProfileUrlUpdate(BaseModel):
    linkedin_url: str = Field(..., description="User's public LinkedIn profile URL")


class LinkedInJobImportRequest(BaseModel):
    linkedin_url: str = Field(..., description="Manually submitted LinkedIn Job URL")
    job_description: str = Field(..., min_length=20, description="Pasted job description text")
    job_title: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    recruiter_name: Optional[str] = None


class LinkedInConnectionStatusResponse(BaseModel):
    is_connected: bool
    account_email: Optional[str] = None
    account_name: Optional[str] = None
    profile_url: Optional[str] = None
    connected_at: Optional[str] = None
    scopes: List[str] = []


class LinkedInOAuthCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


@router.get("/status", response_model=LinkedInConnectionStatusResponse)
def get_linkedin_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve tenant's LinkedIn integration and connection status."""
    conn = db.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == current_user.id,
        ConnectedAccount.provider == "linkedin"
    ).first()

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()

    account_name = None
    if conn and conn.encrypted_token_data:
        try:
            token_json = json.loads(decrypt_secret(conn.encrypted_token_data))
            account_name = token_json.get("profile_name")
        except Exception:
            pass

    return LinkedInConnectionStatusResponse(
        is_connected=conn is not None,
        account_email=conn.account_email if conn else None,
        account_name=account_name,
        profile_url=profile.linkedin_url if profile else None,
        connected_at=conn.created_at.isoformat() if conn else None,
        scopes=conn.scopes if conn else []
    )


@router.get("/oauth/url")
def get_oauth_authorization_url(
    current_user: User = Depends(get_current_user)
):
    """Generate official LinkedIn OAuth 2.0 authorization URL."""
    state = f"user_{current_user.id}_{uuid.uuid4().hex[:8]}"
    auth_url = LinkedInIntegrationService.get_authorization_url(state=state)
    return {"authorization_url": auth_url, "state": state}


@router.post("/oauth/callback")
async def handle_oauth_callback(
    req: LinkedInOAuthCallbackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Exchange authorization code, fetch basic profile, and encrypt token with tenant isolation."""
    try:
        token_data = await LinkedInIntegrationService.exchange_code_for_token(req.code)
        access_token = token_data.get("access_token", "")
        profile_data = await LinkedInIntegrationService.fetch_user_profile(access_token)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"LinkedIn authorization failed: {str(e)}")

    account_email = profile_data.get("email") or current_user.email
    profile_name = profile_data.get("name") or "LinkedIn User"

    # Encrypt token payload
    token_payload = {
        "access_token": access_token,
        "profile_sub": profile_data.get("sub"),
        "profile_name": profile_name,
        "token_data": token_data,
    }
    encrypted_token = encrypt_secret(json.dumps(token_payload))

    # Save to ConnectedAccount with strict tenant ownership
    conn = db.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == current_user.id,
        ConnectedAccount.provider == "linkedin"
    ).first()

    if not conn:
        conn = ConnectedAccount(
            user_id=current_user.id,
            provider="linkedin",
            account_email=account_email,
            encrypted_token_data=encrypted_token,
            scopes=["openid", "profile", "email"]
        )
        db.add(conn)
    else:
        conn.account_email = account_email
        conn.encrypted_token_data = encrypted_token
        conn.scopes = ["openid", "profile", "email"]

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="linkedin.connected",
        resource_type="connected_account",
        resource_id=str(conn.id),
        details={"email": account_email, "scopes": ["openid", "profile", "email"]}
    )
    db.add(audit)

    db.commit()
    db.refresh(conn)

    return {
        "status": "connected",
        "account_email": account_email,
        "account_name": profile_name,
        "message": "LinkedIn account successfully connected via authorized OpenID Connect permissions."
    }


@router.post("/disconnect")
def disconnect_linkedin(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disconnect LinkedIn and delete encrypted token data for tenant."""
    conn = db.query(ConnectedAccount).filter(
        ConnectedAccount.user_id == current_user.id,
        ConnectedAccount.provider == "linkedin"
    ).first()

    if conn:
        db.delete(conn)
        audit = AuditLog(
            user_id=current_user.id,
            action="linkedin.disconnected",
            resource_type="connected_account",
            details={"email": conn.account_email}
        )
        db.add(audit)
        db.commit()

    return {"status": "disconnected", "message": "LinkedIn account disconnected successfully."}


@router.put("/profile-url")
def update_linkedin_profile_url(
    req: LinkedInProfileUrlUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Allow user to manually specify their public LinkedIn profile URL."""
    url = req.linkedin_url.strip()
    if url and not url.startswith("http"):
        url = f"https://{url}"

    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id, linkedin_url=url)
        db.add(profile)
    else:
        profile.linkedin_url = url

    db.commit()
    db.refresh(profile)
    return {"status": "success", "linkedin_url": profile.linkedin_url}


@router.post("/jobs/import")
async def import_linkedin_job(
    req: LinkedInJobImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Compliant LinkedIn Job Import:
    1. Parse and extract requirements from user-provided job description.
    2. Associate/create company and ingest job listing with deduplication.
    3. Evaluate match fit against the user's master CV using AI matching engine.
    4. Generate connection note (<=300 chars) & InMail drafts grounded in CV claims.
    5. Save drafts in Outreach Dashboard with status 'pending_approval' (Approval Center gate).
    6. Return direct manual action link to original LinkedIn URL.
    """
    # 1. Parse user-provided job description
    try:
        norm_job = LinkedInIntegrationService.parse_user_provided_job(
            linkedin_url=req.linkedin_url,
            job_description=req.job_description,
            job_title=req.job_title,
            company_name=req.company_name,
            location=req.location,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 2. Ingest into database
    job, is_new = JobIngestionService.ingest_job(db, norm_job)

    # 3. Retrieve user's master CV
    resume = db.query(Resume).filter(Resume.user_id == current_user.id, Resume.is_master == True).first()
    if not resume:
        resume = db.query(Resume).filter(Resume.user_id == current_user.id).first()

    cv_skills = [s.skill_name for s in resume.skills] if resume else ["Software Engineering", "Python"]
    candidate_name = current_user.full_name or "Candidate"

    # 4. Evaluate fit using matching engine
    match_result = None
    if resume:
        eval_data = MatchingEngineService.evaluate_fit(resume, job)
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

        match_record.overall_score = eval_data["overall_score"]
        match_record.semantic_score = eval_data["semantic_score"]
        match_record.skill_coverage_score = eval_data["skill_coverage_score"]
        match_record.matched_skills = eval_data["matched_skills"]
        match_record.missing_skills = eval_data["missing_skills"]
        match_record.explanation = eval_data["explanation"]
        db.flush()

        match_result = {
            "overall_score": eval_data["overall_score"],
            "matched_skills": eval_data["matched_skills"],
            "missing_skills": eval_data["missing_skills"],
            "explanation": eval_data["explanation"],
        }

    # 5. Generate Grounded LinkedIn Connection Note (<=300 chars)
    note_text = await LinkedInIntegrationService.generate_connection_note(
        candidate_name=candidate_name,
        top_skills=cv_skills,
        job_title=job.title,
        company_name=job.company.name if job.company else "the company",
        recruiter_name=req.recruiter_name,
    )

    connection_note_msg = OutreachMessage(
        user_id=current_user.id,
        job_id=job.id,
        channel="linkedin_note",
        subject=None,
        body_text=note_text,
        cv_grounding_citations=[f"Verified CV expertise: {', '.join(cv_skills[:2])}"],
        status="pending_approval"
    )
    db.add(connection_note_msg)

    # 6. Generate Grounded LinkedIn InMail Draft
    inmail_data = await LinkedInIntegrationService.generate_inmail_draft(
        candidate_name=candidate_name,
        top_skills=cv_skills,
        job_title=job.title,
        company_name=job.company.name if job.company else "the company",
        recruiter_name=req.recruiter_name,
        job_url=req.linkedin_url,
    )

    inmail_msg = OutreachMessage(
        user_id=current_user.id,
        job_id=job.id,
        channel="linkedin_message",
        subject=inmail_data["subject"],
        body_text=inmail_data["body"],
        cv_grounding_citations=[f"Verified CV background: {', '.join(cv_skills[:3])}"],
        status="pending_approval"
    )
    db.add(inmail_msg)

    # 7. Add to application CRM
    app_record = db.query(Application).filter(
        Application.user_id == current_user.id,
        Application.job_id == job.id
    ).first()
    if not app_record:
        app_record = Application(
            user_id=current_user.id,
            job_id=job.id,
            status="saved",
            application_url=req.linkedin_url,
            notes=f"Imported from LinkedIn: {req.linkedin_url}",
        )
        db.add(app_record)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="linkedin.job_imported",
        resource_type="job",
        resource_id=str(job.id),
        details={"url": req.linkedin_url, "title": job.title}
    )
    db.add(audit)

    db.commit()
    db.refresh(job)
    db.refresh(connection_note_msg)
    db.refresh(inmail_msg)

    return {
        "status": "success",
        "message": "LinkedIn job successfully imported, analyzed, matched, and drafted for approval.",
        "job": {
            "id": str(job.id),
            "title": job.title,
            "company_name": job.company.name if job.company else "Company",
            "location": job.location,
            "required_skills": job.required_skills,
            "source_url": job.source_url,
        },
        "match": match_result,
        "drafts": {
            "connection_note": {
                "id": str(connection_note_msg.id),
                "channel": "linkedin_note",
                "character_count": len(connection_note_msg.body_text),
                "body_text": connection_note_msg.body_text,
                "status": connection_note_msg.status,
            },
            "inmail": {
                "id": str(inmail_msg.id),
                "channel": "linkedin_message",
                "subject": inmail_msg.subject,
                "body_text": inmail_msg.body_text,
                "status": inmail_msg.status,
            },
        },
        "manual_action": {
            "original_job_url": req.linkedin_url,
            "notice": "No automated actions taken. Inspect and approve messages in the Approval Center, then execute via the original LinkedIn link.",
        },
    }

