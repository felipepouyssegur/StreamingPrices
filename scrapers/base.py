from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
import re


@dataclass
class ScrapedPlan:
    plan_name: str
    price: float
    currency: str = "ARS"
    billing_period: str = "monthly"
    features: List[str] = field(default_factory=list)


class BaseScraper(ABC):
    service_id: str
    service_name: str

    @abstractmethod
    async def scrape(self, **kwargs) -> List[ScrapedPlan]:
        pass

    def _parse_price(self, text: str) -> Optional[float]:
        """Handles Argentine peso formats: $4.999 / $4,999 / $4.999,00"""
        cleaned = re.sub(r"[^\d.,]", "", text.strip())
        if not cleaned:
            return None
        cleaned = re.sub(r"\.(?=\d{3}($|,))", "", cleaned)
        cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None
