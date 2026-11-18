from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.models.user import User
from backend.app.models.profile import Profile, JobPreference
from backend.app.models.audit import AuditLog
from backend.app.schemas.onboarding import (
    ProfileUpdate,
    JobPreferenceUpdate,
    OnboardingRequest,
    ProfileResponse,
    JobPreferenceResponse,
)
from backend.app.api.deps import get_current_user

router = APIRouter()


@router.get("/profile", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    profile_in: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(Profile).filter(Profile.user_id == current_user.id).first()
    if not profile:
        profile = Profile(user_id=current_user.id)
        db.add(profile)

    update_data = profile_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(profile, field, val)

    audit = AuditLog(
        user_id=current_user.id,
        action="profile.updated",
        resource_type="profile",
        resource_id=str(profile.id),
        details={"updated_fields": list(update_data.keys())}
    )
    db.add(audit)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/preferences", response_model=JobPreferenceResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(JobPreference).filter(JobPreference.user_id == current_user.id).first()
    if not pref:
        pref = JobPreference(user_id=current_user.id)
        db.add(pref)
        db.commit()
        db.refresh(pref)
    return pref


@router.put("/preferences", response_model=JobPreferenceResponse)
def update_preferences(
    pref_in: JobPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    pref = db.query(JobPreference).filter(JobPreference.user_id == current_user.id).first()
    if not pref:
        pref = JobPreference(user_id=current_user.id)
        db.add(pref)

    update_data = pref_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(pref, field, val)

    audit = AuditLog(
        user_id=current_user.id,
        action="preferences.updated",
        resource_type="job_preferences",
        resource_id=str(pref.id),
        details={"employment_type": pref.remote_preference}
    )
    db.add(audit)
    db.commit()
    db.refresh(pref)
    return pref


@router.post("/complete")
def complete_onboarding(
    payload: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atomic update of profile and preferences during initial onboarding step."""
    update_profile(payload.profile, current_user, db)
    update_preferences(payload.preferences, current_user, db)
    return {"message": "Onboarding completed successfully"}

