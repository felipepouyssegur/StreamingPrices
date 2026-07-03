from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional
import re
import logging
from playwright.async_api import async_playwright, Page

logger = logging.getLogger(__name__)


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
    pricing_url: str

    async def scrape(self, headless: bool = True) -> List[ScrapedPlan]:
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(
                headless=headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-blink-features=AutomationControlled",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                locale="es-AR",
                timezone_id="America/Argentina/Buenos_Aires",
                extra_http_headers={"Accept-Language": "es-AR,es;q=0.9,en;q=0.8"},
            )
            await context.add_init_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )
            page = await context.new_page()
            try:
                plans = await self._scrape_page(page)
                logger.info("[%s] Scraped %d plans", self.service_id, len(plans))
                return plans
            except Exception as exc:
                logger.error("[%s] Failed: %s", self.service_id, exc, exc_info=True)
                raise
            finally:
                await browser.close()

    @abstractmethod
    async def _scrape_page(self, page: Page) -> List[ScrapedPlan]:
        pass

    # --- price parsing helpers ---

    _PRICE_RE = re.compile(r"[\d]+(?:[.,\s]\d+)*")

    def _parse_price(self, text: str) -> Optional[float]:
        """
        Handles Argentine peso formats: $4.999 / $4,999 / $4.999,00
        The rule: if a dot is followed by exactly 3 digits at the end → thousands sep.
        """
        cleaned = re.sub(r"[^\d.,]", "", text.strip())
        if not cleaned:
            return None
        # Remove thousands dots (dot followed by 3 digits at end or before comma)
        cleaned = re.sub(r"\.(?=\d{3}($|,))", "", cleaned)
        # Normalize decimal comma
        cleaned = cleaned.replace(",", ".")
        try:
            return float(cleaned)
        except ValueError:
            return None

    async def _find_prices_by_pattern(self, page: Page) -> List[ScrapedPlan]:
        """
        Fallback: search the entire page text for ARS price patterns.
        Returns generic plans named Plan 1, Plan 2, etc.
        """
        content = await page.content()
        # Match patterns like $4.999 or $ 4.999 or ARS 4.999
        matches = re.findall(r"(?:\$|ARS)\s*([\d]{1,2}[.,\s]?\d{3}(?:[.,]\d{2})?)", content)
        seen: set = set()
        plans = []
        for i, m in enumerate(matches):
            price = self._parse_price(m)
            if price and price not in seen and price > 100:
                seen.add(price)
                plans.append(ScrapedPlan(plan_name=f"Plan {i + 1}", price=price))
        return plans
