import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class OutreachGenerateRequest(BaseModel):
    job_id: uuid.UUID
    recruiter_id: Optional[uuid.UUID] = None
    channel: str = Field(..., description="linkedin_note, linkedin_message, cold_email, cover_letter, followup")
    tone: Optional[str] = "professional"  # professional, confident, enthusiastic


class OutreachUpdateRequest(BaseModel):
    subject: Optional[str] = None
    body_text: str


class ApprovalDecisionRequest(BaseModel):
    decision: str = Field(..., description="approved, rejected, edited_and_approved")
    edited_text: Optional[str] = None
    rejection_reason: Optional[str] = None


class OutreachResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: Optional[uuid.UUID] = None
    recruiter_id: Optional[uuid.UUID] = None
    channel: str
    subject: Optional[str] = None
    body_text: str
    cv_grounding_citations: List[str]
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalEventResponse(BaseModel):
    id: uuid.UUID
    outreach_id: uuid.UUID
    decision: str
    original_text: str
    final_text: str
    rejection_reason: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
