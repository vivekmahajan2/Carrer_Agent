from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.billing import Subscription, UsageRecord
from backend.app.api.deps import get_current_user

router = APIRouter()


class UpgradeTierRequest(BaseModel):
    target_tier: str  # pro, enterprise


@router.get("/subscription")
def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current subscription tier, quota limits, and remaining credits."""
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not sub:
        sub = Subscription(user_id=current_user.id, plan_tier="free", status="active")
        db.add(sub)
        db.commit()
        db.refresh(sub)

    plans = {
        "free": {
            "name": "Free Tier",
            "price_usd": 0,
            "monthly_matches": 50,
            "monthly_outreach": 20,
            "features": [
                "1 Master CV upload & parsing",
                "Job & company discovery",
                "Explainable AI match scoring",
                "Standard outreach drafts",
                "Approval Center review"
            ]
        },
        "pro": {
            "name": "CareerPilot Pro",
            "price_usd": 29,
            "monthly_matches": 500,
            "monthly_outreach": 200,
            "features": [
                "Unlimited CV versions & tailoring",
                "Multi-agent LangGraph orchestration",
                "Real-time recruiter intelligence",
                "Automated Gmail drafting",
                "Priority pipeline follow-up tracking"
            ]
        },
        "enterprise": {
            "name": "Executive / Agency",
            "price_usd": 99,
            "monthly_matches": 2000,
            "monthly_outreach": 1000,
            "features": [
                "Multi-client management",
                "Custom LLM API keys",
                "Dedicated sync connectors",
                "Audit exports & API access"
            ]
        }
    }

    return {
        "current_plan": {
            "tier": sub.plan_tier,
            "status": sub.status,
            "monthly_match_quota": sub.monthly_match_quota,
            "monthly_outreach_quota": sub.monthly_outreach_quota,
            "start_date": sub.current_period_start.isoformat() if sub.current_period_start else None
        },
        "available_plans": plans
    }


@router.post("/change-plan")
def change_plan(
    req: UpgradeTierRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update subscription tier in a sandbox/billing-ready architecture."""
    target = req.target_tier.lower()
    if target not in ["free", "pro", "enterprise"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid plan tier")

    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()
    if not sub:
        sub = Subscription(user_id=current_user.id)
        db.add(sub)

    sub.plan_tier = target
    if target == "free":
        sub.monthly_match_quota = 50
        sub.monthly_outreach_quota = 20
    elif target == "pro":
        sub.monthly_match_quota = 500
        sub.monthly_outreach_quota = 200
    elif target == "enterprise":
        sub.monthly_match_quota = 2000
        sub.monthly_outreach_quota = 1000

    db.commit()
    db.refresh(sub)
    return {
        "status": "success",
        "message": f"Successfully updated subscription to {target.capitalize()}",
        "tier": sub.plan_tier,
        "monthly_match_quota": sub.monthly_match_quota
    }

