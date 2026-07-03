"""
Scraper for https://www.impuestito.org/suscripciones
Uses httpx + BeautifulSoup (no browser needed).
Source already aggregates Argentine streaming prices with taxes included.
"""

import re
import logging
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup, Tag

from scrapers.base import BaseScraper, ScrapedPlan

logger = logging.getLogger(__name__)

BASE_URL = "https://www.impuestito.org/suscripciones"

SLUGS = {
    "netflix":   "cual-es-el-precio-de-netflix-con-impuestos-en-argentina",
    "disney":    "cual-es-el-precio-de-disney-plus-con-impuestos-en-argentina",
    "max":       "cual-es-el-precio-de-hbo-max-con-impuestos-en-argentina",
    "amazon":    "cual-es-el-precio-de-amazon-prime-video-con-impuestos-en-argentina",
    "paramount": "cual-es-el-precio-de-paramount-plus-con-impuestos-en-argentina",
    "appletv":   "cual-es-el-precio-de-apple-tv-con-impuestos-en-argentina",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-AR,es;q=0.9",
}

# Matches: $ 9.090 /m  or  $9090/mes  (but NOT /12m)
MONTHLY_RE = re.compile(r"\$\s*([\d.,]+)\s*/\s*m(?:es)?(?!\d)", re.IGNORECASE)
# Matches: $ 54.477 /12m
ANNUAL_RE = re.compile(r"\$\s*([\d.,]+)\s*/\s*12\s*m", re.IGNORECASE)


class ImpuestitoScraper(BaseScraper):
    def __init__(self, service_id: str, service_name: str):
        self.service_id = service_id
        self.service_name = service_name

    async def scrape(self, **kwargs) -> List[ScrapedPlan]:
        slug = SLUGS.get(self.service_id)
        if not slug:
            logger.error("[%s] No slug defined", self.service_id)
            return []

        url = f"{BASE_URL}/{slug}"
        logger.info("[%s] Fetching %s", self.service_id, url)

        async with httpx.AsyncClient(headers=HEADERS, timeout=20, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        plans = self._extract_plans(soup)

        if not plans:
            logger.warning("[%s] No plans found — page structure may have changed", self.service_id)
        else:
            logger.info("[%s] Found %d plans", self.service_id, len(plans))

        return plans

    def _extract_plans(self, soup: BeautifulSoup) -> List[ScrapedPlan]:
        """
        HTML structure on impuestito.org:
          <span title="Netflix Básico" class="...">Netflix Básico</span>   ← plan name
          <span class="text-gray-500 ml-7">$ 11.069 <small>/m</small></span>  ← price
        """
        plans: List[ScrapedPlan] = []
        seen_names: set = set()

        for name_span in soup.select("span[title]"):
            name = name_span.get("title", "").strip()
            if not name or name in seen_names:
                continue

            # Walk up to find the row container, then look for the price span inside it
            container = name_span.parent  # div.flex.items-center
            if container:
                container = container.parent  # outer row div

            price, billing = None, "monthly"
            if container:
                for price_span in container.find_all("span"):
                    classes = " ".join(price_span.get("class", []))
                    if "text-gray-500" in classes and "ml-7" in classes:
                        raw = price_span.get_text().replace("\xa0", " ").strip()
                        price, billing = self._match_price(raw)
                        if price:
                            break

            if name and price and price > 100:
                seen_names.add(name)
                plans.append(ScrapedPlan(
                    plan_name=name,
                    price=price,
                    billing_period=billing,
                ))

        # Fallback: scan page text for price patterns (keeps working if HTML changes)
        if not plans:
            plans = self._fallback_scan(soup)

        return plans

    def _match_price(self, text: str):
        m = MONTHLY_RE.search(text)
        if m:
            return self._parse_price(m.group(1)), "monthly"
        a = ANNUAL_RE.search(text)
        if a:
            return self._parse_price(a.group(1)), "annual"
        return None, "monthly"

    def _fallback_scan(self, soup: BeautifulSoup) -> List[ScrapedPlan]:
        text = soup.get_text()
        seen_prices: set = set()
        plans = []
        for i, m in enumerate(MONTHLY_RE.finditer(text)):
            price = self._parse_price(m.group(1))
            if price and price > 100 and price not in seen_prices:
                seen_prices.add(price)
                plans.append(ScrapedPlan(plan_name=f"Plan {i + 1}", price=price))
        return plans
