from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict):
    user_id: str
    job_id: str
    resume_id: Optional[str]
    recruiter_id: Optional[str]
    channel: str  # linkedin_note, cold_email, cover_letter, followup
    
    # Node outputs
    job_details: Dict[str, Any]
    candidate_profile: Dict[str, Any]
    match_score: Dict[str, Any]
    recruiter_details: Dict[str, Any]
    
    # Outreach & Approval
    generated_subject: Optional[str]
    generated_body: Optional[str]
    cv_citations: List[str]
    approval_status: str  # pending, approved, rejected, edited
    outreach_id: Optional[str]
    
    # Audit & telemetry
    step_history: List[str]
    error: Optional[str]

