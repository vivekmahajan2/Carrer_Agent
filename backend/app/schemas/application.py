import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ApplicationCreate(BaseModel):
    job_id: uuid.UUID
    status: str = "saved"  # saved, draft, approved, submitted, replied, interview, rejected, offer
    notes: Optional[str] = None
    application_url: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    applied_at: Optional[datetime] = None


class FollowupCreate(BaseModel):
    application_id: uuid.UUID
    reminder_date: datetime
    suggested_draft: Optional[str] = None


class FollowupResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    application_id: uuid.UUID
    reminder_date: datetime
    suggested_draft: Optional[str] = None
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ApplicationResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    job_id: uuid.UUID
    status: str
    application_url: Optional[str] = None
    applied_at: Optional[datetime] = None
    notes: Optional[str] = None
    history: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
