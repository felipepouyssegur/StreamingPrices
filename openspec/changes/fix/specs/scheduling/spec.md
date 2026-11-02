## MODIFIED Requirements

### Requirement: Scrape schedule runs on a configurable hourly interval
The system SHALL run the full scrape cycle on a repeating interval defined by `scrape_interval_hours` (default: 24). The old weekly `scrape_day_of_week` setting is removed.

#### Scenario: Scrape fires every N hours
- **WHEN** the app starts with `scrape_enabled=true` and `scrape_interval_hours=24`
- **THEN** the scheduler registers an interval job that fires every 24 hours

#### Scenario: Interval is configurable via environment variable
- **WHEN** the environment sets `SCRAPE_INTERVAL_HOURS=6`
- **THEN** the scheduler fires every 6 hours instead of 24

#### Scenario: Removed setting does not cause startup errors
- **WHEN** `SCRAPE_DAY_OF_WEEK` is present in `.env` (legacy)
- **THEN** the app starts without error (the setting is simply ignored, as pydantic-settings ignores unknown env vars by default)
