import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class ProfileUpdate(BaseModel):
    headline: Optional[str] = None
    target_role: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None


class JobPreferenceUpdate(BaseModel):
    employment_type: str = "full-time"  # full-time, internship, both
    target_roles: List[str] = []
    desired_locations: List[str] = []
    remote_preference: str = "hybrid"  # remote, hybrid, onsite, any
    min_salary_annual: Optional[int] = None
    min_stipend_monthly: Optional[int] = None
    preferred_skills: List[str] = []
    target_industries: List[str] = []


class OnboardingRequest(BaseModel):
    profile: ProfileUpdate
    preferences: JobPreferenceUpdate


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    headline: Optional[str] = None
    target_role: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    github_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class JobPreferenceResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    employment_type: str
    target_roles: List[str]
    desired_locations: List[str]
    remote_preference: str
    min_salary_annual: Optional[int] = None
    min_stipend_monthly: Optional[int] = None
    preferred_skills: List[str]
    target_industries: List[str]

    model_config = ConfigDict(from_attributes=True)
