import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Boolean, Integer, Float, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, GUID

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA-256
    file_type = Column(String(50), nullable=False)  # pdf, docx
    is_master = Column(Boolean, default=False, nullable=False)
    raw_text = Column(Text, nullable=True)
    parsed_json = Column(JSON, default=dict)  # structured profile {skills, education, experience, projects}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="resumes")
    skills = relationship("ResumeSkill", back_populates="resume", cascade="all, delete-orphan")
    job_matches = relationship("JobMatch", back_populates="resume", cascade="all, delete-orphan")


class ResumeSkill(Base):
    __tablename__ = "resume_skills"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    resume_id = Column(GUID(), ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_name = Column(String(100), nullable=False, index=True)
    category = Column(String(100), nullable=True)  # languages, frameworks, cloud, databases, tools, soft_skills
    years_experience = Column(Float, nullable=True)
    proficiency = Column(String(50), nullable=True)  # beginner, intermediate, advanced, expert
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    resume = relationship("Resume", back_populates="skills")

