import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, GUID

class Profile(Base):
    __tablename__ = "profiles"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    headline = Column(String(255), nullable=True)
    target_role = Column(String(255), nullable=True)
    location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    portfolio_url = Column(String(255), nullable=True)
    github_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="profile")


class JobPreference(Base):
    __tablename__ = "job_preferences"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    employment_type = Column(String(50), default="full-time", nullable=False)  # full-time, internship, both
    target_roles = Column(JSON, default=list)  # list of strings e.g. ["AI Engineer", "Full Stack Developer"]
    desired_locations = Column(JSON, default=list)  # ["Bangalore", "San Francisco", "Remote"]
    remote_preference = Column(String(50), default="hybrid", nullable=False)  # remote, hybrid, onsite, any
    min_salary_annual = Column(Integer, nullable=True)
    min_stipend_monthly = Column(Integer, nullable=True)
    preferred_skills = Column(JSON, default=list)
    target_industries = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="job_preferences")

