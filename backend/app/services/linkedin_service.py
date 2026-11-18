import re
import urllib.parse
from typing import Dict, Any, Optional, List
import httpx
from backend.app.core.config import get_settings
from backend.app.core.logging import logger
from backend.app.services.connectors.base import NormalizedJobData
from backend.app.services.llm_provider import get_llm_provider

settings = get_settings()


class LinkedInIntegrationService:
    """Official LinkedIn Integration & Compliant Manual Adapter.
    Strictly follows LinkedIn Developer policies:
    - Uses OpenID Connect standard scopes (openid, profile, email).
    - Never scrapes protected LinkedIn profiles or job pages.
    - Operates through authorized OAuth or user-provided manual import.
    """

    AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    USERINFO_URL = "https://api.linkedin.com/v2/userinfo"

    @classmethod
    def get_authorization_url(cls, state: str) -> str:
        """Constructs official LinkedIn OAuth 2.0 authorization URL."""
        if not settings.LINKEDIN_CLIENT_ID:
            # Clean fallback URL for demo / local configuration
            return f"/api/v1/linkedin/oauth/mock-authorize?state={state}"

        params = {
            "response_type": "code",
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "state": state,
            "scope": "openid profile email",
        }
        return f"{cls.AUTH_URL}?{urllib.parse.urlencode(params)}"

    @classmethod
    async def exchange_code_for_token(cls, code: str) -> Dict[str, Any]:
        """Exchanges authorization code for an OAuth access token."""
        if not settings.LINKEDIN_CLIENT_ID or not settings.LINKEDIN_CLIENT_SECRET:
            # Deterministic mock token for local testing without external credentials
            return {
                "access_token": f"mock_linkedin_token_{code}",
                "expires_in": 5184000,
                "scope": "openid profile email",
                "token_type": "Bearer",
            }

        payload = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.LINKEDIN_REDIRECT_URI,
            "client_id": settings.LINKEDIN_CLIENT_ID,
            "client_secret": settings.LINKEDIN_CLIENT_SECRET,
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                cls.TOKEN_URL,
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if resp.status_code != 200:
                logger.error(f"LinkedIn token exchange error: {resp.text}")
                raise ValueError("Failed to authenticate with LinkedIn API")
            return resp.json()

    @classmethod
    async def fetch_user_profile(cls, access_token: str) -> Dict[str, Any]:
        """Fetches basic profile info using LinkedIn's OpenID Connect UserInfo endpoint."""
        if access_token.startswith("mock_"):
            return {
                "sub": "linkedin-mock-user-12345",
                "name": "LinkedIn Verified User",
                "given_name": "LinkedIn",
                "family_name": "User",
                "email": "linkedin.user@example.com",
                "picture": "https://media.licdn.com/dms/image/default-avatar.png",
            }

        headers = {"Authorization": f"Bearer {access_token}"}
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(cls.USERINFO_URL, headers=headers)
            if resp.status_code != 200:
                logger.error(f"LinkedIn UserInfo error: {resp.text}")
                raise ValueError("Failed to retrieve profile data from LinkedIn")
            return resp.json()

    @classmethod
    def parse_user_provided_job(
        cls,
        linkedin_url: str,
        job_description: str,
        job_title: Optional[str] = None,
        company_name: Optional[str] = None,
        location: Optional[str] = None,
    ) -> NormalizedJobData:
        """Parses and structures user-submitted LinkedIn job description.
        Extracts skills, title, company, requirements, and remote status without scraping.
        """
        # Validate LinkedIn URL format
        parsed_url = urllib.parse.urlparse(linkedin_url)
        if "linkedin.com" not in parsed_url.netloc:
            raise ValueError("URL must be a valid LinkedIn URL (e.g. https://www.linkedin.com/jobs/view/...)")

        # Heuristic title & company extraction if not explicitly provided
        lines = [line.strip() for line in job_description.split("\n") if line.strip()]
        title = job_title or (lines[0] if lines else "Software Engineer")
        company = company_name or (lines[1] if len(lines) > 1 else "Hiring Company")
        job_location = location or "Remote / Multiple Locations"

        # Check remote signals
        desc_lower = job_description.lower()
        is_remote = "remote" in desc_lower or "work from home" in desc_lower or "distributed" in desc_lower

        # Check employment type
        employment_type = "full-time"
        if "intern" in desc_lower or "internship" in desc_lower or "co-op" in desc_lower:
            employment_type = "internship"
        elif "contract" in desc_lower or "freelance" in desc_lower:
            employment_type = "contract"

        # Skill extraction
        known_skills = [
            "Python", "FastAPI", "React", "Next.js", "TypeScript", "JavaScript",
            "Docker", "Kubernetes", "PostgreSQL", "SQL", "Qdrant", "Redis",
            "AWS", "GCP", "Azure", "LangGraph", "LangChain", "RAG", "PyTorch",
            "Git", "CI/CD", "Linux", "REST", "GraphQL", "Tailwind CSS",
        ]
        extracted_skills = []
        for sk in known_skills:
            pattern = r"\b" + re.escape(sk.lower()) + r"\b"
            if re.search(pattern, desc_lower):
                extracted_skills.append(sk)

        # Requirement lines
        requirements = []
        for line in lines:
            line_strip = line.strip(" -*•")
            if len(line_strip) > 15 and any(
                k in line.lower() for k in ["experience", "proficien", "ability", "knowledge", "degree", "years"]
            ):
                if len(requirements) < 8:
                    requirements.append(line_strip)

        if not requirements and lines:
            requirements = [l.strip(" -*•") for l in lines[:4] if len(l) > 10]

        return NormalizedJobData(
            title=title,
            company_name=company,
            company_website=None,
            company_industry="Technology / Software",
            company_size="51-200",
            description=job_description,
            requirements=requirements,
            required_skills=extracted_skills if extracted_skills else ["Python", "Engineering"],
            employment_type=employment_type,
            location=job_location,
            is_remote=is_remote,
            remote_policy="remote" if is_remote else "hybrid",
            salary_min=None,
            salary_max=None,
            salary_currency="USD",
            source_platform="LinkedIn (User Imported)",
            source_url=linkedin_url,
            raw_payload={"import_type": "user_provided_manual_import", "is_compliant": True},
        )

    @classmethod
    async def generate_connection_note(
        cls,
        candidate_name: str,
        top_skills: List[str],
        job_title: str,
        company_name: str,
        recruiter_name: Optional[str] = None,
    ) -> str:
        """Generates a LinkedIn Connection Note strictly under the 300-character platform limit."""
        greeting = f"Hi {recruiter_name}," if recruiter_name else "Hi,"
        skills_str = ", ".join(top_skills[:2]) if top_skills else "software engineering"

        note = f"{greeting} I came across the {job_title} role at {company_name}. With my background in {skills_str}, I would value connecting to follow your team's work."
        if len(note) > 300:
            note = f"{greeting} I noticed the {job_title} opening at {company_name}. With my experience in {skills_str}, I'd love to connect."

        return note[:300]

    @classmethod
    async def generate_inmail_draft(
        cls,
        candidate_name: str,
        top_skills: List[str],
        job_title: str,
        company_name: str,
        recruiter_name: Optional[str] = None,
        job_url: Optional[str] = None,
    ) -> Dict[str, str]:
        """Generates a structured, high-conversion LinkedIn InMail draft grounded in verified CV skills."""
        greeting = f"Hi {recruiter_name}," if recruiter_name else "Dear Hiring Lead,"
        skills_str = ", ".join(top_skills[:3]) if top_skills else "modern software engineering"

        subject = f"Inquiry: {job_title} at {company_name} — {candidate_name}"
        body = (
            f"{greeting}\n\n"
            f"I hope you're having a productive week. I recently reviewed the {job_title} opening at {company_name} "
            f"and was very impressed by your team's direction.\n\n"
            f"My technical background centers on {skills_str}, where I have architected and deployed high-performance "
            f"systems. Given this alignment, I would welcome the opportunity to connect and share how my background "
            f"can add immediate value to your engineering roadmap.\n\n"
            f"Thank you for your time, and I look forward to connecting.\n\n"
            f"Best regards,\n{candidate_name}"
        )

        return {
            "subject": subject,
            "body": body,
            "manual_action_url": job_url or "https://www.linkedin.com/messaging/",
        }

