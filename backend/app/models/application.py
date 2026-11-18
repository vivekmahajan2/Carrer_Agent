import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, GUID

class Application(Base):
    """Job Application CRM Tracker."""
    __tablename__ = "applications"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Statuses: saved, draft, approved, submitted, replied, interview, rejected, offer
    status = Column(String(50), default="saved", nullable=False, index=True)
    application_url = Column(String(512), nullable=True)
    applied_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    history = Column(JSON, default=list)  # list of {timestamp, status, note}
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    followups = relationship("Followup", back_populates="application", cascade="all, delete-orphan")


class Followup(Base):
    """Automated and reminder-based follow-ups."""
    __tablename__ = "followups"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    application_id = Column(GUID(), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, index=True)
    
    reminder_date = Column(DateTime, nullable=False, index=True)
    suggested_draft = Column(Text, nullable=True)
    
    # Status: pending, approved, sent, dismissed
    status = Column(String(50), default="pending", nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="followups")
    application = relationship("Application", back_populates="followups")

