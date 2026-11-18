import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class MatchEvaluationRequest(BaseModel):
    job_id: uuid.UUID
    resume_id: Optional[uuid.UUID] = None  # If omitted, uses master CV


class MatchResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    resume_id: uuid.UUID
    overall_score: float
    semantic_score: float
    skill_coverage_score: float
    experience_fit_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    explanation: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
