from scrapers.netflix import NetflixScraper
from scrapers.disney import DisneyScraper
from scrapers.max_streaming import MaxScraper
from scrapers.amazon import AmazonScraper
from scrapers.paramount import ParamountScraper
from scrapers.apple_tv import AppleTVScraper

ALL_SCRAPERS = [
    NetflixScraper(),
    DisneyScraper(),
    MaxScraper(),
    AmazonScraper(),
    ParamountScraper(),
    AppleTVScraper(),
]

SCRAPER_MAP = {s.service_id: s for s in ALL_SCRAPERS}
