from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.models.user import User
from backend.app.models.profile import Profile, JobPreference
from backend.app.models.billing import Subscription
from backend.app.models.audit import AuditLog
from backend.app.schemas.auth import (
    UserCreate,
    UserLogin,
    Token,
    UserResponse,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user, initialize their profile, preferences, and free subscription."""
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists"
        )

    hashed_pw = get_password_hash(user_in.password)
    new_user = User(
        email=user_in.email.lower(),
        hashed_password=hashed_pw,
        full_name=user_in.full_name,
        is_active=True,
        is_verified=True,  # Default to active/verified for immediate access
        role="user"
    )
    db.add(new_user)
    db.flush()  # to get new_user.id

    # Initialize default profile
    profile = Profile(
        user_id=new_user.id,
        headline="Job Seeker",
        target_role=""
    )
    db.add(profile)

    # Initialize default job preferences
    preferences = JobPreference(
        user_id=new_user.id,
        employment_type="full-time",
        target_roles=[],
        desired_locations=[],
        remote_preference="hybrid",
        preferred_skills=[],
        target_industries=[]
    )
    db.add(preferences)

    # Initialize free tier subscription
    sub = Subscription(
        user_id=new_user.id,
        plan_tier="free",
        status="active",
        monthly_match_quota=50,
        monthly_outreach_quota=20
    )
    db.add(sub)

    # Audit log
    audit = AuditLog(
        user_id=new_user.id,
        action="user.registered",
        resource_type="user",
        resource_id=str(new_user.id),
        details={"email": new_user.email}
    )
    db.add(audit)

    db.commit()
    db.refresh(new_user)

    access_token = create_access_token(subject=str(new_user.id))
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name
    )


@router.post("/login", response_model=Token)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return JWT access token."""
    user = db.query(User).filter(User.email == credentials.email.lower()).first()
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is inactive"
        )

    # Audit log
    audit = AuditLog(
        user_id=user.id,
        action="user.login",
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email}
    )
    db.add(audit)
    db.commit()

    access_token = create_access_token(subject=str(user.id))
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        email=user.email,
        full_name=user.full_name
    )


@router.get("/me")
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get authenticated user's profile, job preferences, and subscription status."""
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    preferences = db.query(JobPreference).filter(JobPreference.user_id == current_user.id).first()
    sub = db.query(Subscription).filter(Subscription.user_id == current_user.id).first()

    return {
        "user": {
            "id": str(current_user.id),
            "email": current_user.email,
            "full_name": current_user.full_name,
            "role": current_user.role,
            "is_active": current_user.is_active,
            "created_at": current_user.created_at.isoformat() if current_user.created_at else None
        },
        "profile": {
            "headline": profile.headline if profile else None,
            "target_role": profile.target_role if profile else None,
            "location": profile.location if profile else None,
            "bio": profile.bio if profile else None,
            "phone": profile.phone if profile else None,
            "linkedin_url": profile.linkedin_url if profile else None,
            "portfolio_url": profile.portfolio_url if profile else None,
            "github_url": profile.github_url if profile else None
        } if profile else None,
        "preferences": {
            "employment_type": preferences.employment_type if preferences else "full-time",
            "target_roles": preferences.target_roles if preferences else [],
            "desired_locations": preferences.desired_locations if preferences else [],
            "remote_preference": preferences.remote_preference if preferences else "hybrid",
            "min_salary_annual": preferences.min_salary_annual if preferences else None,
            "min_stipend_monthly": preferences.min_stipend_monthly if preferences else None,
            "preferred_skills": preferences.preferred_skills if preferences else [],
            "target_industries": preferences.target_industries if preferences else []
        } if preferences else None,
        "subscription": {
            "plan_tier": sub.plan_tier if sub else "free",
            "status": sub.status if sub else "active",
            "monthly_match_quota": sub.monthly_match_quota if sub else 50,
            "monthly_outreach_quota": sub.monthly_outreach_quota if sub else 20
        } if sub else None
    }


@router.post("/password-reset-request")
def request_password_reset(req: PasswordResetRequest, db: Session = Depends(get_db)):
    """Request a password reset link/token."""
    user = db.query(User).filter(User.email == req.email.lower()).first()
    # Always return 200 to prevent email enumeration
    if user:
        reset_token = create_access_token(subject=str(user.id))
        audit = AuditLog(
            user_id=user.id,
            action="user.password_reset_requested",
            resource_type="user",
            resource_id=str(user.id),
            details={"email": user.email}
        )
        db.add(audit)
        db.commit()
        return {"message": "Password reset instructions sent if email exists", "reset_token": reset_token}
    return {"message": "Password reset instructions sent if email exists"}


@router.post("/password-reset-confirm")
def confirm_password_reset(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Confirm password reset with valid token."""
    from backend.app.core.security import decode_access_token
    import uuid
    payload = decode_access_token(req.token)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    try:
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Malformed reset token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = get_password_hash(req.new_password)
    audit = AuditLog(
        user_id=user.id,
        action="user.password_reset_completed",
        resource_type="user",
        resource_id=str(user.id)
    )
    db.add(audit)
    db.commit()
    return {"message": "Password successfully updated"}

