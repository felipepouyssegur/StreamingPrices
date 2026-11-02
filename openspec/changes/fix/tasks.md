## 1. Data Model — add `category` field

- [x] 1.1 Add `category: str = ""` field to `ServiceMeta` in `app/models.py`
- [x] 1.2 Add `category: str` field to `ServiceOut` in `app/models.py`
- [x] 1.3 Update `_build_service_out` in `app/main.py` to pass `category=meta.category` into `ServiceOut`

## 2. Scheduler — switch to interval-based daily scraping

- [x] 2.1 Replace `scrape_day_of_week: str` with `scrape_interval_hours: int = 24` in `app/config.py`; remove `scrape_hour`
- [x] 2.2 In `app/main.py`, import `IntervalTrigger` from apscheduler and replace `CronTrigger(day_of_week=..., hour=...)` with `IntervalTrigger(hours=settings.scrape_interval_hours)`

## 3. Scraper slugs — expand to all 114 services

- [x] 3.1 Add all new slugs to the `SLUGS` dict in `scrapers/impuestito.py` for category "Cine, Series y TV" (Crunchyroll, Kick, Mercado Libre, Mubi, Plex Pass, Rakuten Viki Pass, Stremio, Twitch, ViX Premium, YouTube Premium)
- [x] 3.2 Add slugs for "Música" (Apple Music, Deezer, Amazon Music Unlimited, Spotify, Tidal, Yandex Music, YouTube Music)
- [x] 3.3 Add slugs for "Videojuegos" (Apple Arcade, Chess.com, EA Play, ExitLag, FACEIT, Final Fantasy XIV, GeForce Now, Geoguessr, iRacing, Just Dance Now, Minecraft Realms, Nintendo Switch Online, PlayStation Plus, Ubisoft+, World of Warcraft, Xbox Game Pass)
- [x] 3.4 Add slugs for "Deportes" (F1 TV, NBA League Pass, NFL Game Pass, Triller TV+, UFC Fight Pass, WWE Network)
- [x] 3.5 Add slugs for "Chatbots IA" (ChatGPT, Claude, Copilot, Gemini, Grok, Perplexity, T3.chat)
- [x] 3.6 Add slugs for "Asistentes de Código IA" (Cursor, GitHub Copilot, JetBrains, Tabnine, TRAE AI, Windsurf)
- [x] 3.7 Add slugs for "Vibe Coding" (Bolt, Lovable, v0)
- [x] 3.8 Add slugs for "Generación Visual IA" (Krea AI, Midjourney)
- [x] 3.9 Add slugs for "Hosting, Cloud y Otros" (Bubble.io, GitHub, Nic.ar, Sanity, Starlink, Supabase, Vercel, Webflow)
- [x] 3.10 Add slugs for "Diseño" (Adobe Creative Cloud, Canva, Clipchamp, FigJam, Figma, Framer, Picsart)
- [x] 3.11 Add slugs for "Seguridad" (1Password, Bitwarden, NordVPN)
- [x] 3.12 Add slugs for "Productividad" (Apple One, CapCut, ElevenLabs, Gasti Pro ARS, Gasti Pro USD, Google Workspace, IFTTT, LinkedIn Premium, Microsoft 365, Notion, Obsidian, Proton, TradingView, Zoom)
- [x] 3.13 Add slugs for "Almacenamiento" (Apple iCloud, Dropbox, Google One, OneDrive, Yandex 360)
- [x] 3.14 Add slugs for "Redes Sociales y Chat" (Discord, Meta Verified, Slack, Streamlabs, Telegram, X/Twitter)
- [x] 3.15 Add slugs for "Aprendizaje" (Amazon Audible, Brilliant, Busuu, Duolingo, Kindle Unlimited, Mimo)

## 4. Service catalogue — register all services in DB

- [x] 4.1 Update `_SERVICES` tuple structure in `app/database.py` to include `category` as the last element (6-tuple instead of 5-tuple)
- [x] 4.2 Update the existing 6 entries (netflix, disney, max, amazon, paramount, appletv) to include their category `"Cine, Series y TV"`
- [x] 4.3 Add all new service entries to `_SERVICES` with correct `id`, `name`, `website_url`, `pricing_url`, `logo_url`, and `category`
- [x] 4.4 Update `init_db()` to unpack the 6-tuple and pass `category=` when constructing `ServiceMeta`

## 5. Scraper registration — wire up all new scrapers

- [x] 5.1 Add all 108 new `ImpuestitoScraper(service_id, service_name)` instances to `ALL_SCRAPERS` in `scrapers/__init__.py`

## 6. Verify

- [x] 6.1 Run `python run.py` locally and check `/api/v1/prices` returns 114 services each with a `category` field
- [ ] 6.2 Trigger a manual scrape via `POST /api/v1/scrape` (with API key) and confirm several services across different categories return plans with prices
