from typing import List
from playwright.async_api import Page
from scrapers.base import BaseScraper, ScrapedPlan


class ParamountScraper(BaseScraper):
    service_id = "paramount"
    service_name = "Paramount+"
    pricing_url = "https://www.paramountplus.com/ar/account/signup/pickplan/"

    async def _scrape_page(self, page: Page) -> List[ScrapedPlan]:
        await page.goto(self.pricing_url, wait_until="networkidle", timeout=30000)

        plans = await self._try_plan_cards(page)
        if plans:
            return plans

        return await self._find_prices_by_pattern(page)

    async def _try_plan_cards(self, page: Page) -> List[ScrapedPlan]:
        selectors = [
            (".plan-card", ".plan-name", ".plan-price"),
            ("[data-testid='plan-selection-card']", "[data-testid='plan-name']", "[data-testid='plan-price']"),
            (".subscription-plan", ".plan-title", ".plan-cost"),
        ]

        for card_sel, name_sel, price_sel in selectors:
            try:
                await page.wait_for_selector(card_sel, timeout=8000)
                cards = await page.query_selector_all(card_sel)
                if not cards:
                    continue

                plans = []
                for card in cards:
                    name_el = await card.query_selector(name_sel)
                    price_el = await card.query_selector(price_sel)
                    if not name_el or not price_el:
                        continue
                    name = (await name_el.inner_text()).strip()
                    price = self._parse_price(await price_el.inner_text())
                    if name and price:
                        plans.append(ScrapedPlan(plan_name=name, price=price))

                if plans:
                    return plans
            except Exception:
                continue

        return []
