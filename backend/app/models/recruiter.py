import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, GUID

class Recruiter(Base):
    __tablename__ = "recruiters"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    full_name = Column(String(255), nullable=False, index=True)
    title = Column(String(255), nullable=True)  # Founder, Technical Recruiter, Engineering Manager, HR Lead
    linkedin_url = Column(String(512), nullable=True)
    email = Column(String(255), nullable=True)  # Only populated if publicly published or verified
    is_verified_public = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    company = relationship("Company", back_populates="recruiters")
    evidence = relationship("RecruiterEvidence", back_populates="recruiter", cascade="all, delete-orphan")
    outreach_messages = relationship("OutreachMessage", back_populates="recruiter", cascade="all, delete-orphan")


class RecruiterEvidence(Base):
    """Stores provenance and evidence for publicly discovered recruiters - preventing hallucination."""
    __tablename__ = "recruiter_evidence"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    recruiter_id = Column(GUID(), ForeignKey("recruiters.id", ondelete="CASCADE"), nullable=False, index=True)
    evidence_type = Column(String(100), nullable=False)  # "public_team_page", "blog_post", "job_listing_contact", "public_github"
    public_source_url = Column(String(512), nullable=False)
    snippet = Column(Text, nullable=True)  # exact grounded snippet
    discovered_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    recruiter = relationship("Recruiter", back_populates="evidence")

