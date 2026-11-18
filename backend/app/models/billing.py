import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base, GUID

class Subscription(Base):
    """SaaS Billing & Subscription Tier."""
    __tablename__ = "subscriptions"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    plan_tier = Column(String(50), default="free", nullable=False)  # free, pro, enterprise
    status = Column(String(50), default="active", nullable=False)  # active, canceled, past_due
    monthly_match_quota = Column(Integer, default=50, nullable=False)
    monthly_outreach_quota = Column(Integer, default=20, nullable=False)
    current_period_start = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="subscription")


class UsageRecord(Base):
    """Usage metering records per user."""
    __tablename__ = "usage_records"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False)  # "jobs_discovered", "matches_evaluated", "outreach_generated"
    quantity = Column(Integer, default=1, nullable=False)
    period_key = Column(String(7), nullable=False)  # YYYY-MM
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    user = relationship("User", back_populates="usage_records")

