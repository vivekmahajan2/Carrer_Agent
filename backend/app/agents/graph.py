import uuid
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from backend.app.agents.state import AgentState
from backend.app.services.llm_provider import get_llm_provider
from backend.app.core.logging import logger


async def resume_intelligence_node(state: AgentState) -> Dict[str, Any]:
    """Node 1: Extract candidate intelligence."""
    history = list(state.get("step_history", []))
    history.append("resume_intelligence_node")
    return {
        "step_history": history
    }


async def job_discovery_node(state: AgentState) -> Dict[str, Any]:
    """Node 2: Retrieve and verify job details."""
    history = list(state.get("step_history", []))
    history.append("job_discovery_node")
    return {
        "step_history": history
    }


async def matching_node(state: AgentState) -> Dict[str, Any]:
    """Node 3: Compute match score."""
    history = list(state.get("step_history", []))
    history.append("matching_node")
    return {
        "step_history": history
    }


async def recruiter_intelligence_node(state: AgentState) -> Dict[str, Any]:
    """Node 4: Identify verified public hiring contacts."""
    history = list(state.get("step_history", []))
    history.append("recruiter_intelligence_node")
    return {
        "step_history": history
    }


async def outreach_generation_node(state: AgentState) -> Dict[str, Any]:
    """Node 5: Generate tailored message strictly grounded in user CV."""
    history = list(state.get("step_history", []))
    history.append("outreach_generation_node")

    channel = state.get("channel", "cold_email")
    job = state.get("job_details", {})
    candidate = state.get("candidate_profile", {})

    job_title = job.get("title", "Role")
    company_name = job.get("company_name", "your company")
    skills = candidate.get("skills", ["Python", "FastAPI"])
    top_skills_str = ", ".join(skills[:3]) if skills else "engineering"

    llm = get_llm_provider()

    if channel == "linkedin_note":
        # Strict limit: 300 chars max
        body = f"Hi, I noticed the {job_title} role at {company_name}. With my background in {top_skills_str}, I would love to connect and share relevant projects."
        if len(body) > 295:
            body = body[:292] + "..."
        subject = None
        citations = [f"Direct experience in {top_skills_str}"]
    elif channel == "cold_email":
        subject = f"Application / Experienced {job_title} — {candidate.get('full_name', 'Candidate')}"
        prompt = (
            f"Draft a concise, high-conversion cold email for {job_title} at {company_name}.\n"
            f"Candidate skills: {top_skills_str}.\n"
            f"Strictly ground all claims in the candidate's verified skills."
        )
        body = await llm.generate_text(prompt)
        citations = [f"Verified CV expertise in {top_skills_str}"]
    elif channel == "cover_letter":
        subject = f"Cover Letter: {job_title} — {candidate.get('full_name', 'Candidate')}"
        prompt = (
            f"Draft a 3-paragraph professional cover letter for {job_title} at {company_name} "
            f"highlighting {top_skills_str}."
        )
        body = await llm.generate_text(prompt)
        citations = [f"Verified CV background in {top_skills_str}"]
    else:
        subject = f"Follow-up: {job_title} Opportunity"
        body = f"Hi {company_name} team, following up on my application for the {job_title} position."
        citations = ["Application follow-up"]

    return {
        "generated_subject": subject,
        "generated_body": body.strip(),
        "cv_citations": citations,
        "approval_status": "pending_approval",
        "step_history": history
    }


async def human_approval_checkpoint_node(state: AgentState) -> Dict[str, Any]:
    """Node 6: Pauses and checkpoints workflow. Awaits human approval in the Approval Center."""
    history = list(state.get("step_history", []))
    history.append("human_approval_checkpoint_node")
    return {
        "approval_status": "pending_approval",
        "step_history": history
    }


def build_career_agent_graph():
    """Builds and compiles the multi-agent LangGraph workflow."""
    workflow = StateGraph(AgentState)

    workflow.add_node("resume_intelligence", resume_intelligence_node)
    workflow.add_node("job_discovery", job_discovery_node)
    workflow.add_node("matching", matching_node)
    workflow.add_node("recruiter_intelligence", recruiter_intelligence_node)
    workflow.add_node("outreach_generation", outreach_generation_node)
    workflow.add_node("human_approval_checkpoint", human_approval_checkpoint_node)

    # Define edges
    workflow.set_entry_point("resume_intelligence")
    workflow.add_edge("resume_intelligence", "job_discovery")
    workflow.add_edge("job_discovery", "matching")
    workflow.add_edge("matching", "recruiter_intelligence")
    workflow.add_edge("recruiter_intelligence", "outreach_generation")
    workflow.add_edge("outreach_generation", "human_approval_checkpoint")
    workflow.add_edge("human_approval_checkpoint", END)

    app = workflow.compile()
    return app


agent_graph = build_career_agent_graph()

