import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, GUID

class OutreachMessage(Base):
    """Personalized outreach drafts strictly grounded in user CV."""
    __tablename__ = "outreach_messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    job_id = Column(GUID(), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=True, index=True)
    recruiter_id = Column(GUID(), ForeignKey("recruiters.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Types: linkedin_note (<=300 chars), linkedin_message, cold_email, cover_letter, followup
    channel = Column(String(50), nullable=False)
    subject = Column(String(255), nullable=True)
    body_text = Column(Text, nullable=False)
    cv_grounding_citations = Column(JSON, default=list)  # snippets from user CV that justify claims
    
    # Status: draft, pending_approval, approved, rejected, sent
    status = Column(String(50), default="pending_approval", nullable=False, index=True)
    scheduled_send_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="outreach_messages")
    job = relationship("Job", back_populates="outreach_messages")
    recruiter = relationship("Recruiter", back_populates="outreach_messages")
    approval_events = relationship("ApprovalEvent", back_populates="outreach_message", cascade="all, delete-orphan")


class ApprovalEvent(Base):
    """Immutable audit record of human-in-the-loop decisions."""
    __tablename__ = "approval_events"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    outreach_id = Column(GUID(), ForeignKey("outreach_messages.id", ondelete="CASCADE"), nullable=False, index=True)
    decision = Column(String(50), nullable=False)  # approved, rejected, edited_and_approved
    original_text = Column(Text, nullable=False)
    final_text = Column(Text, nullable=False)
    rejection_reason = Column(Text, nullable=True)
    actor_ip = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    outreach_message = relationship("OutreachMessage", back_populates="approval_events")

