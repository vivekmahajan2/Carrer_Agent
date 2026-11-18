from typing import List, Dict
from backend.app.services.connectors.base import BaseJobConnector
from backend.app.services.connectors.linkedin_connector import LinkedInConnector
from backend.app.services.connectors.connectors import (
    NaukriConnector,
    IndeedConnector,
    InternshalaConnector,
    WellfoundConnector,
    CareerPageConnector
)

class ConnectorRegistry:
    def __init__(self):
        self._connectors: Dict[str, BaseJobConnector] = {
            "linkedin": LinkedInConnector(),
            "naukri": NaukriConnector(),
            "indeed": IndeedConnector(),
            "internshala": InternshalaConnector(),
            "wellfound": WellfoundConnector(),
            "careerpage": CareerPageConnector(),
        }

    def get(self, platform_name: str) -> BaseJobConnector:
        return self._connectors.get(platform_name.lower())

    def list_connectors(self) -> List[BaseJobConnector]:
        return list(self._connectors.values())


registry = ConnectorRegistry()

