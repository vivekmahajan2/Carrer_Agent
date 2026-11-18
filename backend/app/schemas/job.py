import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    company_name: str
    company_website: Optional[str] = None
    company_industry: Optional[str] = None
    title: str
    description: str
    requirements: List[str] = []
    required_skills: List[str] = []
    employment_type: str = "full-time"  # full-time, internship, contract
    location: Optional[str] = None
    is_remote: bool = False
    remote_policy: str = "hybrid"
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    source_url: Optional[str] = None
    platform: str = "Manual"  # LinkedIn, Naukri, Indeed, Internshala, Wellfound, CareerPage, Manual


class JobResponse(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    company_name: Optional[str] = None
    title: str
    description: str
    requirements: List[str]
    required_skills: List[str]
    employment_type: str
    location: Optional[str] = None
    is_remote: bool
    remote_policy: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str
    source_url: Optional[str] = None
    published_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobFilter(BaseModel):
    query: Optional[str] = None
    employment_type: Optional[str] = None
    is_remote: Optional[bool] = None
    location: Optional[str] = None
    company_id: Optional[uuid.UUID] = None
    min_salary: Optional[int] = None
    skip: int = 0
    limit: int = 50
