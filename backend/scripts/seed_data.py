"""
CareerPilot AI — Demo Database Seeder.
Clearly marked as demo data.
"""
import uuid
from datetime import datetime, timezone
from backend.app.core.database import SessionLocal, engine, Base
from backend.app.core.security import get_password_hash
from backend.app.models.user import User
from backend.app.models.profile import Profile, JobPreference
from backend.app.models.billing import Subscription
from backend.app.models.company import Company, CompanySource
from backend.app.models.job import Job, JobSource
from backend.app.models.recruiter import Recruiter, RecruiterEvidence
from backend.app.models.resume import Resume, ResumeSkill
from backend.app.models.match import JobMatch
from backend.app.models.outreach import OutreachMessage
from backend.app.models.application import Application
from backend.app.models.audit import AuditLog
from backend.app.services.job_service import JobIngestionService


def seed_demo_data():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if demo user already exists
        demo_user = db.query(User).filter(User.email == "demo@careerpilot.ai").first()
        if not demo_user:
            demo_user = User(
                email="demo@careerpilot.ai",
                hashed_password=get_password_hash("DemoPilot2026!"),
                full_name="Alex Mercer (Demo)",
                is_active=True,
                is_verified=True,
                role="user"
            )
            db.add(demo_user)
            db.flush()

            # Profile & Preferences
            db.add(Profile(
                user_id=demo_user.id,
                headline="Staff AI & Full-Stack Platform Engineer",
                target_role="Staff AI Engineer",
                location="San Francisco, CA / Remote",
                bio="Experienced engineer specializing in autonomous agent workflows, LangGraph, FastAPI, and Next.js.",
                linkedin_url="https://linkedin.com/in/alexmercer-demo"
            ))
            db.add(JobPreference(
                user_id=demo_user.id,
                employment_type="full-time",
                target_roles=["Staff AI Engineer", "Lead Full Stack Developer"],
                desired_locations=["San Francisco", "New York", "Remote"],
                remote_preference="remote",
                min_salary_annual=170000,
                preferred_skills=["Python", "FastAPI", "Next.js", "LangGraph", "Docker", "PostgreSQL", "Qdrant"],
                target_industries=["Artificial Intelligence", "Developer Tools", "SaaS"]
            ))
            db.add(Subscription(
                user_id=demo_user.id,
                plan_tier="pro",
                status="active",
                monthly_match_quota=500,
                monthly_outreach_quota=200
            ))

            # Master Resume
            demo_cv = Resume(
                user_id=demo_user.id,
                filename="Alex_Mercer_Master_CV.pdf",
                file_path="./uploads/demo_cv.pdf",
                file_hash="demo_hash_alex_mercer_2026",
                file_type="pdf",
                is_master=True,
                raw_text="Alex Mercer - Staff AI Engineer. Built multi-agent pipelines with LangGraph, FastAPI, and Qdrant vector search.",
                parsed_json={
                    "full_name": "Alex Mercer (Demo)",
                    "email": "demo@careerpilot.ai",
                    "skills": [
                        {"skill_name": "Python", "category": "languages", "years_experience": 6.0, "proficiency": "expert"},
                        {"skill_name": "FastAPI", "category": "frameworks", "years_experience": 4.0, "proficiency": "expert"},
                        {"skill_name": "LangGraph", "category": "ai_ml", "years_experience": 2.0, "proficiency": "advanced"},
                        {"skill_name": "Next.js", "category": "frameworks", "years_experience": 4.0, "proficiency": "advanced"},
                        {"skill_name": "PostgreSQL", "category": "databases", "years_experience": 5.0, "proficiency": "advanced"},
                        {"skill_name": "Docker", "category": "cloud_devops", "years_experience": 4.0, "proficiency": "advanced"},
                        {"skill_name": "Qdrant", "category": "databases", "years_experience": 2.0, "proficiency": "intermediate"}
                    ]
                }
            )
            db.add(demo_cv)
            db.flush()

            for sk in demo_cv.parsed_json["skills"]:
                db.add(ResumeSkill(
                    resume_id=demo_cv.id,
                    user_id=demo_user.id,
                    skill_name=sk["skill_name"],
                    category=sk["category"],
                    years_experience=sk["years_experience"],
                    proficiency=sk["proficiency"]
                ))

        # Seed Companies & Jobs
        companies_seed = [
            {
                "name": "CognitiveFlow AI (Demo)",
                "domain": "cognitiveflow.ai",
                "website": "https://cognitiveflow.ai",
                "industry": "Artificial Intelligence",
                "size": "51-200",
                "headquarters": "San Francisco, CA",
                "description": "Building autonomous cognitive agents for enterprise automation.",
                "tech_stack": ["Python", "FastAPI", "LangGraph", "Qdrant", "Next.js"],
                "hiring_signals": {"actively_hiring": True, "open_roles": 4, "recent_funding": "Series B ($35M)"}
            },
            {
                "name": "DevPulse Platforms (Demo)",
                "domain": "devpulse.io",
                "website": "https://devpulse.io",
                "industry": "Developer Productivity",
                "size": "11-50",
                "headquarters": "Remote",
                "description": "Developer platform optimizing PR workflows and AI code intelligence.",
                "tech_stack": ["Next.js", "TypeScript", "Tailwind CSS", "PostgreSQL", "Docker"],
                "hiring_signals": {"actively_hiring": True, "open_roles": 2, "recent_funding": "Series A ($12M)"}
            }
        ]

        for c_data in companies_seed:
            comp = db.query(Company).filter(Company.name == c_data["name"]).first()
            if not comp:
                comp = Company(**c_data)
                db.add(comp)
                db.flush()

                db.add(CompanySource(
                    company_id=comp.id,
                    source_name="Demo Seed",
                    source_url="https://careerpilot.ai/demo",
                    provenance_metadata={"is_demo": True}
                ))

                # Recruiter
                recruiter = Recruiter(
                    company_id=comp.id,
                    full_name=f"Elena Rostova ({comp.name})",
                    title="Head of Talent & Engineering Hiring",
                    linkedin_url="https://linkedin.com/in/elena-rostova-demo",
                    email=f"talent@{comp.domain}",
                    is_verified_public=True
                )
                db.add(recruiter)
                db.flush()

                db.add(RecruiterEvidence(
                    recruiter_id=recruiter.id,
                    evidence_type="public_team_page",
                    public_source_url=f"https://{comp.domain}/about/team",
                    snippet="Official talent acquisition lead verified from public team directory."
                ))

        db.commit()
        print("Demo seed completed successfully. Demo credentials: demo@careerpilot.ai / DemoPilot2026!")
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()

