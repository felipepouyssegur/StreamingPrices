import re
from typing import List
from playwright.async_api import Page
from scrapers.base import BaseScraper, ScrapedPlan


class AppleTVScraper(BaseScraper):
    service_id = "appletv"
    service_name = "Apple TV+"
    pricing_url = "https://www.apple.com/ar/apple-tv-plus/"

    async def _scrape_page(self, page: Page) -> List[ScrapedPlan]:
        await page.goto(self.pricing_url, wait_until="networkidle", timeout=30000)

        plans = await self._try_price_elements(page)
        if plans:
            return plans

        return await self._find_prices_by_pattern(page)

    async def _try_price_elements(self, page: Page) -> List[ScrapedPlan]:
        # Apple TV+ has a single plan; price appears in a pricing section
        selectors = [
            ".pricing-main .price",
            "[data-module-template='pricing-main'] .price",
            ".section-pricing .price-point",
            ".price-point-base",
        ]

        for sel in selectors:
            try:
                el = await page.wait_for_selector(sel, timeout=6000)
                if not el:
                    continue
                price = self._parse_price(await el.inner_text())
                if price:
                    return [ScrapedPlan(plan_name="Apple TV+", price=price)]
            except Exception:
                continue

        # Last resort: look for the price in page text via regex
        content = await page.inner_text("body")
        match = re.search(r"(\$\s*[\d.,]+)\s*/\s*mes", content, re.IGNORECASE)
        if match:
            price = self._parse_price(match.group(1))
            if price:
                return [ScrapedPlan(plan_name="Apple TV+", price=price)]

        return []
