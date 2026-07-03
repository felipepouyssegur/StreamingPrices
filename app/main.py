import json
import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import get_settings
from app.database import get_session, init_db, mark_scrape_error, save_scrape_results
from app.models import (
    ManualPriceIn,
    PlanOut,
    PriceRecord,
    PricesResponse,
    ScrapeResult,
    ServiceMeta,
    ServiceOut,
)
from scrapers import ALL_SCRAPERS, SCRAPER_MAP
from scrapers.base import ScrapedPlan

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


# ── helpers ────────────────────────────────────────────────────────────────


async def _run_scraper(service_id: str) -> ScrapeResult:
    scraper = SCRAPER_MAP.get(service_id)
    if not scraper:
        return ScrapeResult(service_id=service_id, status="error", plans_saved=0, error="Unknown service")

    settings = get_settings()
    try:
        plans = await scraper.scrape(headless=settings.headless)
        if not plans:
            raise ValueError("No plans found — selectors may need updating")
        save_scrape_results(service_id, plans)
        return ScrapeResult(service_id=service_id, status="ok", plans_saved=len(plans))
    except Exception as exc:
        error = str(exc)
        mark_scrape_error(service_id, error)
        logger.error("Scraper failed for %s: %s", service_id, error)
        return ScrapeResult(service_id=service_id, status="error", plans_saved=0, error=error)


async def _run_all_scrapers():
    logger.info("Running scheduled scrape for all services")
    for scraper in ALL_SCRAPERS:
        await _run_scraper(scraper.service_id)
    logger.info("Scheduled scrape complete")


def _build_service_out(meta: ServiceMeta, records: List[PriceRecord]) -> ServiceOut:
    plans = [
        PlanOut(
            plan_name=r.plan_name,
            price=r.price,
            currency=r.currency,
            billing_period=r.billing_period,
            features=json.loads(r.features) if r.features else [],
            is_manual=r.is_manual,
            scraped_at=r.scraped_at,
        )
        for r in sorted(records, key=lambda x: x.price)
    ]
    return ServiceOut(
        id=meta.id,
        name=meta.name,
        website_url=meta.website_url,
        logo_url=meta.logo_url,
        last_scraped_at=meta.last_scraped_at,
        scrape_status=meta.scrape_status,
        plans=plans,
    )


# ── auth ───────────────────────────────────────────────────────────────────


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    settings = get_settings()
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header")


# ── lifespan ───────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    settings = get_settings()
    scheduler.add_job(
        _run_all_scrapers,
        CronTrigger(day_of_week=settings.scrape_day_of_week, hour=settings.scrape_hour, minute=0),
        id="weekly_scrape",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started — weekly scrape on %s at %02d:00", settings.scrape_day_of_week, settings.scrape_hour)
    yield
    scheduler.shutdown(wait=False)


# ── app ────────────────────────────────────────────────────────────────────


app = FastAPI(
    title="Streaming Prices AR",
    description="API de precios de servicios de streaming en Argentina",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── public endpoints ───────────────────────────────────────────────────────


@app.get("/api/v1/prices", response_model=PricesResponse, tags=["prices"])
def get_all_prices(session: Session = Depends(get_session)):
    """Devuelve los precios actuales de todos los servicios."""
    services_meta = session.exec(select(ServiceMeta)).all()
    result = []
    for meta in services_meta:
        records = session.exec(
            select(PriceRecord).where(
                PriceRecord.service_id == meta.id,
                PriceRecord.is_current == True,
            )
        ).all()
        result.append(_build_service_out(meta, list(records)))
    return PricesResponse(generated_at=datetime.utcnow(), services=result)


@app.get("/api/v1/prices/{service_id}", response_model=ServiceOut, tags=["prices"])
def get_service_prices(service_id: str, session: Session = Depends(get_session)):
    """Devuelve los precios actuales de un servicio específico."""
    meta = session.get(ServiceMeta, service_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    records = session.exec(
        select(PriceRecord).where(
            PriceRecord.service_id == service_id,
            PriceRecord.is_current == True,
        )
    ).all()
    return _build_service_out(meta, list(records))


@app.get("/api/v1/history/{service_id}", response_model=List[PlanOut], tags=["prices"])
def get_price_history(service_id: str, limit: int = 50, session: Session = Depends(get_session)):
    """Devuelve el historial de precios de un servicio (todos los registros, no solo el actual)."""
    meta = session.get(ServiceMeta, service_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    records = session.exec(
        select(PriceRecord)
        .where(PriceRecord.service_id == service_id)
        .order_by(PriceRecord.scraped_at.desc())
        .limit(limit)
    ).all()
    return [
        PlanOut(
            plan_name=r.plan_name,
            price=r.price,
            currency=r.currency,
            billing_period=r.billing_period,
            features=json.loads(r.features) if r.features else [],
            is_manual=r.is_manual,
            scraped_at=r.scraped_at,
        )
        for r in records
    ]


# ── admin endpoints (require API key) ─────────────────────────────────────


@app.post("/api/v1/scrape", response_model=List[ScrapeResult], tags=["admin"], dependencies=[Depends(require_api_key)])
async def scrape_all(background_tasks: BackgroundTasks):
    """Dispara el scraping de todos los servicios en background."""
    background_tasks.add_task(_run_all_scrapers)
    return [ScrapeResult(service_id=s.service_id, status="queued", plans_saved=0) for s in ALL_SCRAPERS]


@app.post("/api/v1/scrape/{service_id}", response_model=ScrapeResult, tags=["admin"], dependencies=[Depends(require_api_key)])
async def scrape_one(service_id: str):
    """Dispara el scraping de un servicio específico (espera el resultado)."""
    if service_id not in SCRAPER_MAP:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")
    return await _run_scraper(service_id)


@app.put("/api/v1/prices/{service_id}", tags=["admin"], dependencies=[Depends(require_api_key)])
def manual_price_override(
    service_id: str,
    plans: List[ManualPriceIn],
    session: Session = Depends(get_session),
):
    """
    Permite cargar precios manualmente cuando el scraper falla.
    Reemplaza los precios actuales del servicio.
    """
    meta = session.get(ServiceMeta, service_id)
    if not meta:
        raise HTTPException(status_code=404, detail=f"Service '{service_id}' not found")

    scraped = [
        ScrapedPlan(
            plan_name=p.plan_name,
            price=p.price,
            currency=p.currency,
            billing_period=p.billing_period,
            features=p.features,
        )
        for p in plans
    ]
    save_scrape_results(service_id, scraped, is_manual=True)
    return {"status": "ok", "plans_saved": len(scraped)}


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok", "timestamp": datetime.utcnow()}
