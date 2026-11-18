import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, GUID

class AuditLog(Base):
    """Audit events for security and compliance."""
    __tablename__ = "audit_logs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # "user.login", "cv.upload", "outreach.approved"
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="audit_logs")


class ConnectedAccount(Base):
    """OAuth tokens and integrations (e.g., Gmail)."""
    __tablename__ = "connected_accounts"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # "google_gmail", "linkedin"
    account_email = Column(String(255), nullable=True)
    encrypted_token_data = Column(Text, nullable=False)
    scopes = Column(JSON, default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="connected_accounts")


class AgentRun(Base):
    """Tracks multi-agent LangGraph workflow execution runs."""
    __tablename__ = "agent_runs"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    thread_id = Column(String(100), unique=True, index=True, nullable=False)
    workflow_type = Column(String(100), default="job_match_outreach", nullable=False)
    status = Column(String(50), default="running", nullable=False)  # running, waiting_approval, completed, failed
    current_node = Column(String(100), nullable=True)
    state_payload = Column(JSON, default=dict)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

