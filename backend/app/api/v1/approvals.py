import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.outreach import OutreachMessage, ApprovalEvent
from backend.app.models.application import Application
from backend.app.models.audit import AuditLog
from backend.app.schemas.outreach import ApprovalDecisionRequest, OutreachResponse, ApprovalEventResponse
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.get("/pending", response_model=List[OutreachResponse])
def get_pending_approvals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve all drafts waiting for human approval."""
    return (
        db.query(OutreachMessage)
        .filter(OutreachMessage.user_id == current_user.id, OutreachMessage.status == "pending_approval")
        .order_by(OutreachMessage.created_at.desc())
        .all()
    )


@router.post("/{outreach_id}/decision", response_model=OutreachResponse)
def submit_approval_decision(
    outreach_id: uuid.UUID,
    decision_req: ApprovalDecisionRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve, reject, or edit and approve an outreach message."""
    msg = db.query(OutreachMessage).filter(
        OutreachMessage.id == outreach_id,
        OutreachMessage.user_id == current_user.id
    ).first()
    if not msg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")

    decision = decision_req.decision.lower()
    if decision not in ["approved", "rejected", "edited_and_approved"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Decision must be 'approved', 'rejected', or 'edited_and_approved'"
        )

    original_text = msg.body_text
    final_text = decision_req.edited_text if (decision_req.edited_text and decision == "edited_and_approved") else original_text

    if decision in ["approved", "edited_and_approved"]:
        msg.status = "approved"
        msg.body_text = final_text
    else:
        msg.status = "rejected"

    # Create immutable ApprovalEvent audit
    client_ip = request.client.host if request.client else "unknown"
    approval_event = ApprovalEvent(
        user_id=current_user.id,
        outreach_id=msg.id,
        decision=decision,
        original_text=original_text,
        final_text=final_text,
        rejection_reason=decision_req.rejection_reason,
        actor_ip=client_ip
    )
    db.add(approval_event)

    # If approved and attached to a job, advance application status if an application exists
    if msg.status == "approved" and msg.job_id:
        app_record = db.query(Application).filter(
            Application.user_id == current_user.id,
            Application.job_id == msg.job_id
        ).first()
        if app_record:
            app_record.status = "approved"
        else:
            app_record = Application(
                user_id=current_user.id,
                job_id=msg.job_id,
                status="approved",
                history=[{"timestamp": datetime.now(timezone.utc).isoformat(), "status": "approved", "note": "Outreach approved"}]
            )
            db.add(app_record)

    audit = AuditLog(
        user_id=current_user.id,
        action=f"outreach.{decision}",
        resource_type="outreach_message",
        resource_id=str(msg.id),
        ip_address=client_ip,
        details={"decision": decision, "channel": msg.channel}
    )
    db.add(audit)

    db.commit()
    db.refresh(msg)
    return msg


@router.get("/history", response_model=List[ApprovalEventResponse])
def get_approval_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve immutable approval audit trail for the tenant."""
    events = (
        db.query(ApprovalEvent)
        .filter(ApprovalEvent.user_id == current_user.id)
        .order_by(ApprovalEvent.created_at.desc())
        .limit(100)
        .all()
    )
    return events

