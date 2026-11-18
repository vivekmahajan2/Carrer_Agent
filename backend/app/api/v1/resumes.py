import os
import uuid
import hashlib
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from backend.app.core.config import get_settings
from backend.app.core.database import get_db
from backend.app.core.logging import logger
from backend.app.models.user import User
from backend.app.models.resume import Resume, ResumeSkill
from backend.app.models.audit import AuditLog
from backend.app.schemas.resume import (
    ResumeResponse,
    SkillItem,
    MasterCVSelectRequest,
)
from backend.app.services.resume_parser import ResumeParserService
from backend.app.api.deps import get_current_user

router = APIRouter()
settings = get_settings()

os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


@router.post("/upload", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a PDF or DOCX CV, extract text & structured skills, and store tenant-isolated resume."""
    filename = file.filename or "resume.pdf"
    extension = os.path.splitext(filename)[1].lower()
    
    if extension not in [".pdf", ".docx", ".doc"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Please upload a PDF (.pdf) or Word document (.docx)."
        )

    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB."
        )

    file_hash = hashlib.sha256(content).hexdigest()

    # Tenant-safe storage: save under user ID
    user_upload_dir = os.path.join(settings.UPLOAD_DIR, str(current_user.id))
    os.makedirs(user_upload_dir, exist_ok=True)
    saved_filename = f"{uuid.uuid4()}{extension}"
    file_path = os.path.join(user_upload_dir, saved_filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Extract text & parse
    try:
        raw_text = ResumeParserService.extract_text(file_path, extension)
        parsed_data = ResumeParserService.parse_structured_data(raw_text)
    except Exception as e:
        logger.error(f"Error parsing resume {filename}: {str(e)}", exc_info=True)
        raw_text = ""
        parsed_data = {"error": "Failed to parse document text", "skills": []}

    # Check if this should be master (if user has no resumes yet)
    existing_count = db.query(Resume).filter(Resume.user_id == current_user.id).count()
    is_master = (existing_count == 0)

    new_resume = Resume(
        user_id=current_user.id,
        filename=filename,
        file_path=file_path,
        file_hash=file_hash,
        file_type="pdf" if "pdf" in extension else "docx",
        is_master=is_master,
        raw_text=raw_text,
        parsed_json=parsed_data
    )
    db.add(new_resume)
    db.flush()

    # Persist extracted skills to resume_skills table
    for s in parsed_data.get("skills", []):
        skill_row = ResumeSkill(
            resume_id=new_resume.id,
            user_id=current_user.id,
            skill_name=s.get("skill_name", "General"),
            category=s.get("category", "general"),
            years_experience=s.get("years_experience", 1.0),
            proficiency=s.get("proficiency", "intermediate")
        )
        db.add(skill_row)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="resume.uploaded",
        resource_type="resume",
        resource_id=str(new_resume.id),
        details={"filename": filename, "file_hash": file_hash, "is_master": is_master}
    )
    db.add(audit)

    db.commit()
    db.refresh(new_resume)
    return new_resume


@router.get("/", response_model=List[ResumeResponse])
def list_resumes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all resumes uploaded by the authenticated user."""
    return db.query(Resume).filter(Resume.user_id == current_user.id).order_by(Resume.created_at.desc()).all()


@router.get("/{resume_id}", response_model=ResumeResponse)
def get_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single CV by ID (strictly tenant-isolated)."""
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
    return resume


@router.put("/{resume_id}/select-master", response_model=ResumeResponse)
def select_master_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Designate this resume as the master CV for match operations."""
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Unmark any other master resumes
    db.query(Resume).filter(Resume.user_id == current_user.id).update({"is_master": False})
    resume.is_master = True

    audit = AuditLog(
        user_id=current_user.id,
        action="resume.master_selected",
        resource_type="resume",
        resource_id=str(resume.id)
    )
    db.add(audit)
    db.commit()
    db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resume(
    resume_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a resume and clean up its file on disk."""
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    file_path = resume.file_path
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Could not remove file {file_path}: {e}")

    db.delete(resume)
    db.commit()
    return None


@router.put("/{resume_id}/skills", response_model=ResumeResponse)
def update_resume_skills(
    resume_id: uuid.UUID,
    skills: List[SkillItem],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update or edit the extracted skills for a resume."""
    resume = db.query(Resume).filter(Resume.id == resume_id, Resume.user_id == current_user.id).first()
    if not resume:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")

    # Replace resume_skills rows
    db.query(ResumeSkill).filter(ResumeSkill.resume_id == resume.id).delete()
    for s in skills:
        db.add(ResumeSkill(
            resume_id=resume.id,
            user_id=current_user.id,
            skill_name=s.skill_name,
            category=s.category or "general",
            years_experience=s.years_experience or 1.0,
            proficiency=s.proficiency or "intermediate"
        ))

    # Also update parsed_json skills array
    parsed = dict(resume.parsed_json or {})
    parsed["skills"] = [s.model_dump() for s in skills]
    resume.parsed_json = parsed

    db.commit()
    db.refresh(resume)
    return resume

