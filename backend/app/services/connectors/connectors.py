import datetime
from typing import List
from backend.app.services.connectors.base import BaseJobConnector, NormalizedJobData


class NaukriConnector(BaseJobConnector):
    """Naukri Connector Interface."""
    @property
    def platform_name(self) -> str:
        return "Naukri"

    async def fetch_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        employment_type: str = "full-time",
        limit: int = 10
    ) -> List[NormalizedJobData]:
        return [
            NormalizedJobData(
                title="Senior Backend Python Developer",
                company_name="InnovateScale Labs",
                company_website="https://innovatescale.in",
                company_industry="Enterprise Software",
                company_size="201-500",
                description="Looking for an experienced Backend Engineer to design scalable microservices using FastAPI, Celery, and PostgreSQL.",
                requirements=[
                    "4+ years with Python & SQLAlchemy",
                    "Strong background in distributed messaging (Celery, Redis)",
                    "Knowledge of containerization and Linux environments"
                ],
                required_skills=["Python", "FastAPI", "SQLAlchemy", "PostgreSQL", "Celery", "Redis"],
                employment_type="full-time",
                location="Bangalore, India",
                is_remote=False,
                remote_policy="hybrid",
                salary_min=1800000,
                salary_max=2800000,
                salary_currency="INR",
                source_platform="Naukri",
                source_url="https://www.naukri.com/job-listings-innovatescale-senior-python",
                published_date=datetime.datetime.now(datetime.timezone.utc),
                raw_payload={"compliance_verified": True}
            )
        ]


class IndeedConnector(BaseJobConnector):
    """Indeed Connector Interface."""
    @property
    def platform_name(self) -> str:
        return "Indeed"

    async def fetch_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        employment_type: str = "full-time",
        limit: int = 10
    ) -> List[NormalizedJobData]:
        return [
            NormalizedJobData(
                title="AI / ML Engineer",
                company_name="Veritas Intelligence",
                company_website="https://veritasintel.com",
                company_industry="Machine Learning",
                company_size="11-50",
                description="We are building agentic workflows for fintech applications. You will deploy LLM pipelines with LangChain and vector retrieval systems.",
                requirements=[
                    "2+ years experience building RAG or Agent pipelines",
                    "Proficiency with Python, PyTorch or Transformers",
                    "Familiarity with FastAPI backend services"
                ],
                required_skills=["Python", "LangChain", "FastAPI", "RAG", "Qdrant"],
                employment_type="full-time",
                location="Austin, TX / Remote",
                is_remote=True,
                remote_policy="remote",
                salary_min=135000,
                salary_max=175000,
                salary_currency="USD",
                source_platform="Indeed",
                source_url="https://www.indeed.com/viewjob?jk=veritas-ai-engineer-101",
                published_date=datetime.datetime.now(datetime.timezone.utc),
                raw_payload={"compliance_verified": True}
            )
        ]


class InternshalaConnector(BaseJobConnector):
    """Internshala Internship & Entry-level Connector Interface."""
    @property
    def platform_name(self) -> str:
        return "Internshala"

    async def fetch_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        employment_type: str = "internship",
        limit: int = 10
    ) -> List[NormalizedJobData]:
        return [
            NormalizedJobData(
                title="AI & Full Stack Engineering Intern",
                company_name="HyperLoop AI Labs",
                company_website="https://hyperlooplabs.dev",
                company_industry="Early Stage AI Startup",
                company_size="1-10",
                description="Exciting 6-month internship building agentic workflows, responsive Next.js frontend interfaces, and LLM integrations. PPO available upon completion.",
                requirements=[
                    "Strong foundation in Python and JavaScript/TypeScript",
                    "Hands-on project experience with Next.js or FastAPI",
                    "Eagerness to learn vector databases and agent frameworks"
                ],
                required_skills=["Python", "FastAPI", "Next.js", "TypeScript", "Tailwind CSS"],
                employment_type="internship",
                location="Bangalore / Remote",
                is_remote=True,
                remote_policy="remote",
                salary_min=30000,
                salary_max=50000,
                salary_currency="INR",
                source_platform="Internshala",
                source_url="https://internshala.com/internship/detail/hyperloop-ai-internship",
                published_date=datetime.datetime.now(datetime.timezone.utc),
                raw_payload={"stipend_type": "monthly", "has_ppo": True}
            )
        ]


class WellfoundConnector(BaseJobConnector):
    """Wellfound (AngelList) Startup Connector Interface."""
    @property
    def platform_name(self) -> str:
        return "Wellfound"

    async def fetch_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        employment_type: str = "full-time",
        limit: int = 10
    ) -> List[NormalizedJobData]:
        return [
            NormalizedJobData(
                title="Lead Frontend Engineer (Next.js)",
                company_name="FlowMetrics AI",
                company_website="https://flowmetrics.ai",
                company_industry="Developer Tools",
                company_size="11-50",
                description="Build high-performance web products, sleek design systems with Tailwind CSS, and delightful user experiences for AI engineers.",
                requirements=[
                    "3+ years building production Next.js / React apps",
                    "Deep knowledge of TypeScript, state management, and Tailwind CSS",
                    "Obsession with performance and UI polish inspired by Linear/Stripe"
                ],
                required_skills=["Next.js", "React", "TypeScript", "Tailwind CSS"],
                employment_type="full-time",
                location="San Francisco / Remote",
                is_remote=True,
                remote_policy="remote",
                salary_min=150000,
                salary_max=190000,
                salary_currency="USD",
                source_platform="Wellfound",
                source_url="https://wellfound.com/company/flowmetrics-ai/jobs/lead-frontend",
                published_date=datetime.datetime.now(datetime.timezone.utc),
                raw_payload={"equity_offered": "0.5% - 1.5%"}
            )
        ]


class CareerPageConnector(BaseJobConnector):
    """Company Direct Career Page Connector Interface."""
    @property
    def platform_name(self) -> str:
        return "CareerPage"

    async def fetch_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        employment_type: str = "full-time",
        limit: int = 10
    ) -> List[NormalizedJobData]:
        return [
            NormalizedJobData(
                title="Platform Engineer (PostgreSQL & Cloud)",
                company_name="CloudMatrix Systems",
                company_website="https://cloudmatrix.dev",
                company_industry="Cloud Infrastructure",
                company_size="51-200",
                description="Architect robust database clusters, multi-tenant isolation schemas, and high-availability systems on AWS & Docker.",
                requirements=[
                    "Expert knowledge of PostgreSQL performance tuning and RLS",
                    "Strong background in Docker, Linux, and Terraform",
                    "Experience with Python or Go backend services"
                ],
                required_skills=["PostgreSQL", "Docker", "Linux", "Python", "AWS"],
                employment_type="full-time",
                location="Seattle, WA / Hybrid",
                is_remote=False,
                remote_policy="hybrid",
                salary_min=155000,
                salary_max=195000,
                salary_currency="USD",
                source_platform="CareerPage",
                source_url="https://cloudmatrix.dev/careers/platform-engineer",
                published_date=datetime.datetime.now(datetime.timezone.utc),
                raw_payload={"direct_applicant_portal": True}
            )
        ]

