from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.job import Job
from backend.app.models.match import JobMatch
from backend.app.models.outreach import OutreachMessage
from backend.app.models.application import Application
from backend.app.models.company import Company
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.get("/dashboard")
def get_dashboard_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Compute real-time dashboard analytics from real database state."""
    # 1. Total jobs in database
    total_jobs_discovered = db.query(Job).filter(Job.is_active == True).count()
    total_companies = db.query(Company).count()

    # 2. User's evaluated matches
    user_matches_query = db.query(JobMatch).filter(JobMatch.user_id == current_user.id)
    total_matches_evaluated = user_matches_query.count()
    matching_jobs_count = user_matches_query.filter(JobMatch.overall_score >= 70.0).count()
    
    avg_score_row = db.query(func.avg(JobMatch.overall_score)).filter(JobMatch.user_id == current_user.id).scalar()
    avg_match_score = round(float(avg_score_row), 1) if avg_score_row else 0.0

    # 3. Pending approvals
    pending_approvals = db.query(OutreachMessage).filter(
        OutreachMessage.user_id == current_user.id,
        OutreachMessage.status == "pending_approval"
    ).count()

    # 4. Total outreach drafts & sent
    total_outreach = db.query(OutreachMessage).filter(OutreachMessage.user_id == current_user.id).count()
    sent_outreach = db.query(OutreachMessage).filter(
        OutreachMessage.user_id == current_user.id,
        OutreachMessage.status.in_(["approved", "sent"])
    ).count()

    # 5. Application CRM breakdown
    apps = db.query(Application).filter(Application.user_id == current_user.id).all()
    total_applications = len(apps)

    status_counts = {
        "saved": 0,
        "draft": 0,
        "approved": 0,
        "submitted": 0,
        "replied": 0,
        "interview": 0,
        "rejected": 0,
        "offer": 0
    }
    for a in apps:
        if a.status in status_counts:
            status_counts[a.status] += 1

    # Real calculated conversion metrics
    interview_count = status_counts["interview"]
    offer_count = status_counts["offer"]
    replies_count = status_counts["replied"] + status_counts["interview"] + status_counts["offer"]
    
    response_rate = round((replies_count / total_applications * 100), 1) if total_applications > 0 else 0.0

    return {
        "metrics": {
            "jobs_discovered": total_jobs_discovered,
            "companies_tracked": total_companies,
            "matching_jobs": matching_jobs_count,
            "total_matches_evaluated": total_matches_evaluated,
            "average_match_score": avg_match_score,
            "pending_approvals": pending_approvals,
            "total_outreach_drafts": total_outreach,
            "sent_or_approved_outreach": sent_outreach,
            "total_applications": total_applications,
            "interviews": interview_count,
            "offers": offer_count,
            "response_rate_percent": response_rate
        },
        "pipeline": status_counts
    }

