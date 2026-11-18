import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, GUID

class JobMatch(Base):
    """Explainable CV to Job match score and breakdown."""
    __tablename__ = "job_matches"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    resume_id = Column(GUID(), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    
    overall_score = Column(Float, nullable=False)  # 0.0 to 100.0
    semantic_score = Column(Float, nullable=False)  # 0.0 to 100.0
    skill_coverage_score = Column(Float, nullable=False)  # 0.0 to 100.0
    experience_fit_score = Column(Float, default=100.0)
    
    matched_skills = Column(JSON, default=list)  # ["Python", "FastAPI"]
    missing_skills = Column(JSON, default=list)  # ["Kubernetes", "GraphQL"]
    
    # Detailed explainability
    explanation = Column(JSON, default=dict)  # {"summary": "Strong backend fit...", "highlights": [...], "concerns": [...]}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="job_matches")
    job = relationship("Job", back_populates="matches")
    resume = relationship("Resume", back_populates="job_matches")

