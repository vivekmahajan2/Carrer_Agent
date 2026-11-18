from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class NormalizedJobData(BaseModel):
    title: str
    company_name: str
    company_website: Optional[str] = None
    company_industry: Optional[str] = None
    company_size: Optional[str] = None
    description: str
    requirements: List[str] = []
    required_skills: List[str] = []
    employment_type: str = "full-time"  # full-time, internship, contract
    location: Optional[str] = None
    is_remote: bool = False
    remote_policy: str = "hybrid"  # remote, hybrid, onsite
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    source_platform: str
    source_url: Optional[str] = None
    published_date: Optional[datetime] = None
    raw_payload: Dict[str, Any] = {}


class NormalizedCompanyData(BaseModel):
    name: str
    domain: Optional[str] = None
    website: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    headquarters: Optional[str] = None
    description: Optional[str] = None
    tech_stack: List[str] = []
    hiring_signals: Dict[str, Any] = {}
    source_name: str
    source_url: Optional[str] = None


class BaseJobConnector(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Name of the discovery source, e.g. 'LinkedIn', 'Naukri', 'Indeed'."""
        pass

    @abstractmethod
    async def fetch_jobs(
        self,
        keywords: List[str],
        locations: List[str],
        employment_type: str = "full-time",
        limit: int = 20
    ) -> List[NormalizedJobData]:
        """Fetch and normalize job listings adhering strictly to permitted public APIs and limits."""
        pass


class BaseCompanyConnector(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str:
        pass

    @abstractmethod
    async def fetch_companies(
        self,
        industries: List[str],
        locations: List[str],
        limit: int = 10
    ) -> List[NormalizedCompanyData]:
        pass

