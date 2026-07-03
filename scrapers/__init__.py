from scrapers.impuestito import ImpuestitoScraper

ALL_SCRAPERS = [
    ImpuestitoScraper("netflix",   "Netflix"),
    ImpuestitoScraper("disney",    "Disney+"),
    ImpuestitoScraper("max",       "Max"),
    ImpuestitoScraper("amazon",    "Amazon Prime Video"),
    ImpuestitoScraper("paramount", "Paramount+"),
    ImpuestitoScraper("appletv",   "Apple TV+"),
]

SCRAPER_MAP = {s.service_id: s for s in ALL_SCRAPERS}
