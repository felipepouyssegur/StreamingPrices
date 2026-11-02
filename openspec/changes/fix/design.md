## Context

The app currently tracks 6 video streaming services via a single `ImpuestitoScraper` that is already generic — it takes any `service_id` and looks up the corresponding URL slug from a dict. The scraper, API, and DB layers all scale cleanly to N services with no architectural changes. impuestito.org has grown to 120+ services across 16 categories; only the catalogue data (slugs, service metadata) needs to be expanded.

The `ServiceMeta` model lacks a `category` field, which makes it impossible for the Flutter app to group or filter the ~114 services meaningfully. The scheduler fires weekly via APScheduler's `CronTrigger(day_of_week=...)`, but Argentine peso prices can change daily.

## Goals / Non-Goals

**Goals:**
- Expand service catalogue from 6 → 114 entries covering all impuestito.org categories (except Adults and Créditos para Videojuegos)
- Add `category` field to DB, API responses, and service registration
- Switch scheduler to run every N hours (default 24) instead of weekly

**Non-Goals:**
- Changing scraper parsing logic — existing `span[title]` / `span.text-gray-500.ml-7` selectors remain unchanged
- Adding a `/api/v1/prices?category=X` filter endpoint — Flutter can filter client-side given the category field
- Migrating historical price records — only current records matter; history carries forward naturally

## Decisions

### 1. Service catalogue as static code, not a DB table

**Decision:** Keep `_SERVICES` as a hardcoded list in `database.py` seeded at `init_db()`.

**Why:** The source of truth is impuestito.org's URL structure, which changes rarely. A DB-managed catalogue would add admin endpoints with no benefit. Static code is reviewable and diff-able.

**Alternative considered:** A `services.json` config file — rejected because it adds a loading step with no gain over a Python list.

### 2. `category` as a plain string field on `ServiceMeta`

**Decision:** Add `category: str = ""` to `ServiceMeta` and expose it in `ServiceOut`.

**Why:** Keeps the model flat and simple. Categories are stable strings ("Cine, Series y TV", "Música", etc.) matching impuestito.org's own groupings. No foreign key needed for 16 fixed values.

**Alternative considered:** A separate `Category` table — rejected as over-engineered for a fixed list.

### 3. `IntervalTrigger` for daily scheduling

**Decision:** Replace `CronTrigger(day_of_week=..., hour=...)` with `IntervalTrigger(hours=scrape_interval_hours)`.

**Why:** Interval-based scheduling is simpler for "run every X hours" semantics. `CronTrigger` without `day_of_week` works too but requires more config fields.

**New config field:** `scrape_interval_hours: int = 24` (replaces `scrape_day_of_week: str`). Old `scrape_hour` is removed.

### 4. DB migration strategy

**Decision:** Drop and recreate the SQLite DB on deploy (no `ALTER TABLE`).

**Why:** Render's free tier uses ephemeral storage — the DB is already wiped on every redeploy. The app auto-scrapes on startup when the DB is empty, so data repopulates automatically within minutes of deploy.

## Risks / Trade-offs

- **[Risk] HTML selectors changed on impuestito.org** → The fallback text scanner (`_fallback_scan`) catches price data even if class names change. A failed scrape sets `scrape_status=error` on that service so the Flutter app can show stale-data indicators.
- **[Risk] Some new services have no ARS pricing** → Scraper returns 0 plans; service shows as `pending` in API. No crash, just empty plans array.
- **[Risk] 114 sequential HTTP requests per scrape cycle** → At ~0.5s per request, one full cycle takes ~60s. This is fine for a 24h interval. Run in background task, never blocking an API request.

## Migration Plan

1. Update code (models, db, scrapers, config, main)
2. Push to Render — deploy wipes SQLite DB automatically
3. On startup, `init_db()` seeds all 114 services; auto-scrape populates prices
4. Verify `/api/v1/prices` returns `category` field and ~114 services
