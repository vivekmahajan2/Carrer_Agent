import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class SkillItem(BaseModel):
    skill_name: str
    category: Optional[str] = "general"
    years_experience: Optional[float] = None
    proficiency: Optional[str] = "intermediate"


class ResumeParsedData(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    summary: Optional[str] = None
    skills: List[SkillItem] = []
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    projects: List[Dict[str, Any]] = []
    certifications: List[str] = []


class ResumeResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    file_type: str
    is_master: bool
    parsed_json: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MasterCVSelectRequest(BaseModel):
    resume_id: uuid.UUID
