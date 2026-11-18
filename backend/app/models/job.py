import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, GUID

class Job(Base):
    __tablename__ = "jobs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    requirements = Column(JSON, default=list)  # list of requirement strings
    required_skills = Column(JSON, default=list)  # ["Python", "Docker", "SQL"]
    employment_type = Column(String(50), default="full-time", nullable=False)  # full-time, internship, contract
    location = Column(String(255), nullable=True)
    is_remote = Column(Boolean, default=False, nullable=False)
    remote_policy = Column(String(50), default="hybrid")  # remote, hybrid, onsite
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    salary_currency = Column(String(10), default="USD")
    source_url = Column(String(512), nullable=True)
    published_date = Column(DateTime, nullable=True)
    deduplication_hash = Column(String(64), unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    company = relationship("Company", back_populates="jobs")
    sources = relationship("JobSource", back_populates="job", cascade="all, delete-orphan")
    matches = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")
    outreach_messages = relationship("OutreachMessage", back_populates="job", cascade="all, delete-orphan")


class JobSource(Base):
    __tablename__ = "job_sources"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    job_id = Column(GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    platform = Column(String(100), nullable=False)  # LinkedIn, Naukri, Indeed, Internshala, Wellfound, CareerPage, Manual
    raw_payload = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    job = relationship("Job", back_populates="sources")

