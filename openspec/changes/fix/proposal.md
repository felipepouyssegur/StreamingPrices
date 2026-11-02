## Why

impuestito.org expanded from ~6 video streaming services to 120+ services across 16 categories (music, gaming, sports, AI tools, design, productivity, etc.), leaving the app tracking only 5% of what's available. The scraper infrastructure already handles any service generically — only the service catalogue needs to be updated. Daily scraping (vs. weekly) is also needed since Argentine peso prices change frequently.

## What Changes

- Add ~108 new services to the catalogue covering all categories on impuestito.org (excluding Adults and Créditos para Videojuegos)
- Add a `category` field to `ServiceMeta` (DB) and `ServiceOut` (API response) so Flutter can filter/group by category
- Change the scheduler from weekly (`CronTrigger` with `day_of_week`) to daily via a configurable interval setting
- No changes to scraper parsing logic — it already works generically for any impuestito.org service URL

## Capabilities

### New Capabilities

- `service-catalogue`: Full service catalogue with 114 entries across 16 categories, each with a `category` field

### Modified Capabilities

- `scheduling`: Scrape schedule changes from weekly-only to daily (configurable interval in hours)

## Impact

- `app/models.py`: Add `category: str` to `ServiceMeta` and `ServiceOut`
- `app/database.py`: Update `_SERVICES` tuple structure to include category; add ~108 new service entries
- `scrapers/impuestito.py`: Add ~108 new slugs to `SLUGS` dict
- `scrapers/__init__.py`: Add ~108 new `ImpuestitoScraper` instances to `ALL_SCRAPERS`
- `app/config.py`: Replace `scrape_day_of_week` with `scrape_interval_hours` (default: 24)
- `app/main.py`: Replace `CronTrigger(day_of_week=...)` with `IntervalTrigger(hours=scrape_interval_hours)`
- **DB migration**: SQLite schema change requires dropping and recreating the DB (acceptable — Render resets on deploy anyway)
- API response `ServiceOut` gains `category` field — additive, non-breaking for existing Flutter clients
