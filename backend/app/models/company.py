import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, GUID

class Company(Base):
    __tablename__ = "companies"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    domain = Column(String(255), unique=True, index=True, nullable=True)
    website = Column(String(512), nullable=True)
    industry = Column(String(255), nullable=True, index=True)
    size = Column(String(50), nullable=True)  # "1-10", "11-50", "51-200", "201-500", "500+"
    headquarters = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tech_stack = Column(JSON, default=list)  # ["Python", "FastAPI", "React", "Postgres"]
    hiring_signals = Column(JSON, default=dict)  # {"actively_hiring": True, "recent_funding": "Series A", "open_roles_count": 5}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    sources = relationship("CompanySource", back_populates="company", cascade="all, delete-orphan")
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")
    recruiters = relationship("Recruiter", back_populates="company", cascade="all, delete-orphan")


class CompanySource(Base):
    __tablename__ = "company_sources"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    company_id = Column(GUID(), ForeignKey("companies.id", ondelete="CASCADE"), nullable=False, index=True)
    source_name = Column(String(100), nullable=False)  # "LinkedIn", "Wellfound", "YCombinator", "Manual"
    source_url = Column(String(512), nullable=True)
    provenance_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    company = relationship("Company", back_populates="sources")

