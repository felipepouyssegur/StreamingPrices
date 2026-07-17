"""
Scraper for impuestito.org
Uses httpx + BeautifulSoup (no browser needed).
Source already aggregates Argentine streaming prices with taxes included.

Prices are read from the JSON-LD (schema.org Product/offers) block that the
site embeds server-side. That is far more stable than scraping the hydrated
React markup, whose CSS classes change frequently.
"""

import re
import json
import logging
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup, Tag

from scrapers.base import BaseScraper, ScrapedPlan

logger = logging.getLogger(__name__)

BASE_URL = "https://www.impuestito.org/suscripciones"

SLUGS = {
    # Cine, Series y TV
    "netflix":       "cual-es-el-precio-de-netflix-con-impuestos-en-argentina",
    "disney":        "cual-es-el-precio-de-disney-plus-con-impuestos-en-argentina",
    "max":           "cual-es-el-precio-de-hbo-max-con-impuestos-en-argentina",
    "amazon":        "cual-es-el-precio-de-amazon-prime-video-con-impuestos-en-argentina",
    "paramount":     "cual-es-el-precio-de-paramount-plus-con-impuestos-en-argentina",
    "appletv":       "cual-es-el-precio-de-apple-tv-con-impuestos-en-argentina",
    "crunchyroll":   "cual-es-el-precio-de-crunchyroll-con-impuestos-en-argentina",
    "kick":          "cual-es-el-precio-de-kick-con-impuestos-en-argentina",
    "mercadolibre":  "cual-es-el-precio-de-mercado-libre-con-impuestos-en-argentina",
    "mubi":          "cual-es-el-precio-de-mubi-con-impuestos-en-argentina",
    "plex":          "cual-es-el-precio-de-plex-pass-con-impuestos-en-argentina",
    "viki":          "cual-es-el-precio-de-rakuten-viki-pass-con-impuestos-en-argentina",
    "stremio":       "cual-es-el-precio-de-stremio-con-impuestos-en-argentina",
    "twitch":        "cual-es-el-precio-de-twitch-con-impuestos-en-argentina",
    "vix":           "cual-es-el-precio-de-vix-premium-con-impuestos-en-argentina",
    "youtube":       "cual-es-el-precio-de-youtube-premium-con-impuestos-en-argentina",
    # Música
    "applemusic":    "cual-es-el-precio-de-apple-music-con-impuestos-en-argentina",
    "deezer":        "cual-es-el-precio-de-deezer-con-impuestos-en-argentina",
    "amazonmusic":   "cual-es-el-precio-de-amazon-music-unlimited-con-impuestos-en-argentina",
    "spotify":       "cual-es-el-precio-de-spotify-con-impuestos-en-argentina",
    "tidal":         "cual-es-el-precio-de-tidal-con-impuestos-en-argentina",
    "yandexmusic":   "cual-es-el-precio-de-yandex-music-con-impuestos-en-argentina",
    "youtubemusic":  "cual-es-el-precio-de-youtube-music-con-impuestos-en-argentina",
    # Videojuegos
    "applearcade":   "cual-es-el-precio-de-apple-arcade-con-impuestos-en-argentina",
    "chess":         "cual-es-el-precio-de-chess-com-con-impuestos-en-argentina",
    "eaplay":        "cual-es-el-precio-de-ea-play-con-impuestos-en-argentina",
    "exitlag":       "cual-es-el-precio-de-exitlag-con-impuestos-en-argentina",
    "faceit":        "cual-es-el-precio-de-faceit-con-impuestos-en-argentina",
    "ffxiv":         "cual-es-el-precio-de-final-fantasy-xiv-con-impuestos-en-argentina",
    "geforcenow":    "cual-es-el-precio-de-geforce-now-con-impuestos-en-argentina",
    "geoguessr":     "cual-es-el-precio-de-geoguessr-con-impuestos-en-argentina",
    "iracing":       "cual-es-el-precio-de-iracing-con-impuestos-en-argentina",
    "justdance":     "cual-es-el-precio-de-just-dance-now-con-impuestos-en-argentina",
    "minecraft":     "cual-es-el-precio-de-minecraft-realms-con-impuestos-en-argentina",
    "nintendo":      "cual-es-el-precio-de-nintendo-switch-online-con-impuestos-en-argentina",
    "playstation":   "cual-es-el-precio-de-playstation-plus-con-impuestos-en-argentina",
    "ubisoft":       "cual-es-el-precio-de-ubisoft-plus-con-impuestos-en-argentina",
    "wow":           "cual-es-el-precio-de-world-of-warcraft-con-impuestos-en-argentina",
    "xbox":          "cual-es-el-precio-de-xbox-game-pass-con-impuestos-en-argentina",
    # Deportes
    "f1tv":          "cual-es-el-precio-de-f1-tv-con-impuestos-en-argentina",
    "nba":           "cual-es-el-precio-de-nba-league-pass-con-impuestos-en-argentina",
    "nfl":           "cual-es-el-precio-de-nfl-game-pass-con-impuestos-en-argentina",
    "trillertv":     "cual-es-el-precio-de-triller-tv-plus-con-impuestos-en-argentina",
    "ufc":           "cual-es-el-precio-de-ufc-fight-pass-con-impuestos-en-argentina",
    "wwe":           "cual-es-el-precio-de-wwe-network-con-impuestos-en-argentina",
    # Chatbots IA
    "chatgpt":       "cual-es-el-precio-de-chatgpt-con-impuestos-en-argentina",
    "claude":        "cual-es-el-precio-de-claude-con-impuestos-en-argentina",
    "copilot":       "cual-es-el-precio-de-copilot-con-impuestos-en-argentina",
    "gemini":        "cual-es-el-precio-de-gemini-con-impuestos-en-argentina",
    "grok":          "cual-es-el-precio-de-grok-con-impuestos-en-argentina",
    "perplexity":    "cual-es-el-precio-de-perplexity-con-impuestos-en-argentina",
    "t3chat":        "cual-es-el-precio-de-t3-chat-con-impuestos-en-argentina",
    # Asistentes de Código IA
    "cursor":        "cual-es-el-precio-de-cursor-con-impuestos-en-argentina",
    "githubcopilot": "cual-es-el-precio-de-github-copilot-con-impuestos-en-argentina",
    "jetbrains":     "cual-es-el-precio-de-jetbrains-con-impuestos-en-argentina",
    "tabnine":       "cual-es-el-precio-de-tabnine-con-impuestos-en-argentina",
    "traeai":        "cual-es-el-precio-de-trae-ai-con-impuestos-en-argentina",
    "windsurf":      "cual-es-el-precio-de-windsurf-con-impuestos-en-argentina",
    # Vibe Coding
    "bolt":          "cual-es-el-precio-de-bolt-con-impuestos-en-argentina",
    "lovable":       "cual-es-el-precio-de-lovable-con-impuestos-en-argentina",
    "v0":            "cual-es-el-precio-de-v0-con-impuestos-en-argentina",
    # Generación Visual IA
    "krea":          "cual-es-el-precio-de-krea-ai-con-impuestos-en-argentina",
    "midjourney":    "cual-es-el-precio-de-midjourney-con-impuestos-en-argentina",
    # Hosting, Cloud y Otros
    "bubble":        "cual-es-el-precio-de-bubble-io-con-impuestos-en-argentina",
    "github":        "cual-es-el-precio-de-github-con-impuestos-en-argentina",
    "nicar":         "cual-es-el-precio-de-nic-ar-con-impuestos-en-argentina",
    "sanity":        "cual-es-el-precio-de-sanity-con-impuestos-en-argentina",
    "starlink":      "cual-es-el-precio-de-starlink-con-impuestos-en-argentina",
    "supabase":      "cual-es-el-precio-de-supabase-con-impuestos-en-argentina",
    "vercel":        "cual-es-el-precio-de-vercel-con-impuestos-en-argentina",
    "webflow":       "cual-es-el-precio-de-webflow-con-impuestos-en-argentina",
    # Diseño
    "adobe":         "cual-es-el-precio-de-adobe-creative-cloud-con-impuestos-en-argentina",
    "canva":         "cual-es-el-precio-de-canva-con-impuestos-en-argentina",
    "clipchamp":     "cual-es-el-precio-de-clipchamp-con-impuestos-en-argentina",
    "figjam":        "cual-es-el-precio-de-figjam-con-impuestos-en-argentina",
    "figma":         "cual-es-el-precio-de-figma-con-impuestos-en-argentina",
    "framer":        "cual-es-el-precio-de-framer-con-impuestos-en-argentina",
    "picsart":       "cual-es-el-precio-de-picsart-con-impuestos-en-argentina",
    # Seguridad
    "onepassword":   "cual-es-el-precio-de-1password-con-impuestos-en-argentina",
    "bitwarden":     "cual-es-el-precio-de-bitwarden-con-impuestos-en-argentina",
    "nordvpn":       "cual-es-el-precio-de-nordvpn-con-impuestos-en-argentina",
    # Productividad
    "appleone":      "cual-es-el-precio-de-apple-one-con-impuestos-en-argentina",
    "capcut":        "cual-es-el-precio-de-capcut-con-impuestos-en-argentina",
    "elevenlabs":    "cual-es-el-precio-de-evenlabs-con-impuestos-en-argentina",
    "gastipro":      "cual-es-el-precio-de-gasti-pro-ars-con-impuestos-en-argentina",
    "gastitprousd":  "cual-es-el-precio-de-gasti-pro-usd-con-impuestos-en-argentina",
    "gworkspace":    "cual-es-el-precio-de-google-workspace-con-impuestos-en-argentina",
    "ifttt":         "cual-es-el-precio-de-ifttt-con-impuestos-en-argentina",
    "linkedin":      "cual-es-el-precio-de-linkedin-premium-con-impuestos-en-argentina",
    "microsoft365":  "cual-es-el-precio-de-microsoft-365-con-impuestos-en-argentina",
    "notion":        "cual-es-el-precio-de-notion-con-impuestos-en-argentina",
    "obsidian":      "cual-es-el-precio-de-obsidian-con-impuestos-en-argentina",
    "proton":        "cual-es-el-precio-de-proton-con-impuestos-en-argentina",
    "tradingview":   "cual-es-el-precio-de-trading-view-con-impuestos-en-argentina",
    "zoom":          "cual-es-el-precio-de-zoom-con-impuestos-en-argentina",
    # Almacenamiento
    "icloud":        "cual-es-el-precio-de-apple-icloud-con-impuestos-en-argentina",
    "dropbox":       "cual-es-el-precio-de-dropbox-con-impuestos-en-argentina",
    "googleone":     "cual-es-el-precio-de-google-one-con-impuestos-en-argentina",
    "onedrive":      "cual-es-el-precio-de-one-drive-con-impuestos-en-argentina",
    "yandex360":     "cual-es-el-precio-de-yandex-360-con-impuestos-en-argentina",
    # Redes Sociales y Chat
    "discord":       "cual-es-el-precio-de-discord-con-impuestos-en-argentina",
    "metaverified":  "cual-es-el-precio-de-meta-verified-con-impuestos-en-argentina",
    "slack":         "cual-es-el-precio-de-slack-con-impuestos-en-argentina",
    "streamlabs":    "cual-es-el-precio-de-streamlabs-con-impuestos-en-argentina",
    "telegram":      "cual-es-el-precio-de-telegram-con-impuestos-en-argentina",
    "twitter":       "cual-es-el-precio-de-x-twitter-con-impuestos-en-argentina",
    # Aprendizaje
    "audible":       "cual-es-el-precio-de-amazon-audible-con-impuestos-en-argentina",
    "brilliant":     "cual-es-el-precio-de-brilliant-con-impuestos-en-argentina",
    "busuu":         "cual-es-el-precio-de-busuu-con-impuestos-en-argentina",
    "duolingo":      "cual-es-el-precio-de-duolingo-con-impuestos-en-argentina",
    "kindle":        "cual-es-el-precio-de-kindle-unlimited-con-impuestos-en-argentina",
    "mimo":          "cual-es-el-precio-de-mimo-con-impuestos-en-argentina",
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
        Primary source: JSON-LD schema.org Product with an `offers` array, e.g.
          {"@type":"Offer","name":"Netflix Básico","price":8999,
           "priceCurrency":"ARS","description":"Facturación cada 1 mes(es)"}
        """
        plans = self._extract_from_jsonld(soup)

        # Fallback: scan visible text for price patterns if JSON-LD is missing
        if not plans:
            logger.info("[%s] JSON-LD empty — trying text fallback", self.service_id)
            plans = self._fallback_scan(soup)

        return plans

    def _extract_from_jsonld(self, soup: BeautifulSoup) -> List[ScrapedPlan]:
        plans: List[ScrapedPlan] = []
        seen: set = set()

        for script in soup.find_all("script", type="application/ld+json"):
            raw = script.string or script.get_text()
            if not raw:
                continue
            try:
                data = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                continue

            # JSON-LD may be a single object or a list of objects
            for node in data if isinstance(data, list) else [data]:
                if not isinstance(node, dict):
                    continue
                offers = node.get("offers")
                if not offers:
                    continue
                if isinstance(offers, dict):
                    offers = [offers]

                for offer in offers:
                    if not isinstance(offer, dict):
                        continue
                    name = (offer.get("name") or "").strip()
                    price = self._coerce_price(offer.get("price"))
                    if not name or price is None or price <= 0:
                        continue

                    billing = self._billing_from_description(offer.get("description", ""))
                    currency = (offer.get("priceCurrency") or "ARS").strip() or "ARS"

                    key = (name, price, billing)
                    if key in seen:
                        continue
                    seen.add(key)

                    plans.append(ScrapedPlan(
                        plan_name=name,
                        price=price,
                        currency=currency,
                        billing_period=billing,
                    ))

        return plans

    @staticmethod
    def _coerce_price(value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value).replace(",", "."))
        except ValueError:
            return None

    @staticmethod
    def _billing_from_description(desc: str) -> str:
        """'Facturación cada 12 mes(es)' → 'annual'."""
        m = re.search(r"cada\s+(\d+)\s*mes", desc, re.IGNORECASE)
        months = int(m.group(1)) if m else 1
        return {
            1: "monthly",
            3: "quarterly",
            6: "biannual",
            12: "annual",
        }.get(months, f"every_{months}_months")

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
