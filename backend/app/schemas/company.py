import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class CompanyCreate(BaseModel):
    name: str
    domain: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    headquarters: Optional[str] = None
    description: Optional[str] = None
    tech_stack: List[str] = []
    hiring_signals: Dict[str, Any] = {}
    source_name: Optional[str] = "Manual"
    source_url: Optional[str] = None


class CompanyResponse(BaseModel):
    id: uuid.UUID
    name: str
    domain: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    headquarters: Optional[str] = None
    description: Optional[str] = None
    tech_stack: List[str]
    hiring_signals: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
