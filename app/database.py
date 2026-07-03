import json
from datetime import datetime
from typing import List
from sqlmodel import Session, SQLModel, create_engine, select

from app.config import get_settings
from app.models import PriceRecord, ServiceMeta
from scrapers.base import ScrapedPlan

_engine = None

# Default service catalogue (id, name, website, pricing_url, logo_url)
_SERVICES = [
    ("netflix",   "Netflix",            "https://www.netflix.com/ar",          "https://www.netflix.com/ar/signup/planform",                          "https://cdn.worldvectorlogo.com/logos/netflix-4.svg"),
    ("disney",    "Disney+",            "https://www.disneyplus.com/es-ar",    "https://www.disneyplus.com/es-ar/subscribe",                          "https://cdn.worldvectorlogo.com/logos/disney-plus-1.svg"),
    ("max",       "Max",                "https://www.max.com/ar/es",           "https://www.max.com/ar/es/plans",                                     "https://cdn.worldvectorlogo.com/logos/hbo-max-1.svg"),
    ("amazon",    "Amazon Prime Video", "https://www.amazon.com.ar/prime",     "https://www.amazon.com.ar/amazonprime",                               "https://cdn.worldvectorlogo.com/logos/prime-video-1.svg"),
    ("paramount", "Paramount+",         "https://www.paramountplus.com/ar",    "https://www.paramountplus.com/ar/account/signup/",                    "https://cdn.worldvectorlogo.com/logos/paramount-plus-1.svg"),
    ("appletv",   "Apple TV+",          "https://www.apple.com/ar/apple-tv-plus/", "https://www.apple.com/ar/apple-tv-plus/",                        "https://cdn.worldvectorlogo.com/logos/apple-tv-plus-logo.svg"),
]


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
        _engine = create_engine(settings.database_url, connect_args=connect_args)
    return _engine


def init_db():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        for sid, name, website, pricing, logo in _SERVICES:
            if not session.get(ServiceMeta, sid):
                session.add(ServiceMeta(
                    id=sid, name=name, website_url=website,
                    pricing_url=pricing, logo_url=logo,
                ))
        session.commit()


def get_session():
    with Session(get_engine()) as session:
        yield session


def save_scrape_results(service_id: str, plans: List[ScrapedPlan], is_manual: bool = False):
    with Session(get_engine()) as session:
        # Mark old records as not current
        old = session.exec(
            select(PriceRecord).where(
                PriceRecord.service_id == service_id,
                PriceRecord.is_current == True,
            )
        ).all()
        for rec in old:
            rec.is_current = False

        now = datetime.utcnow()
        for plan in plans:
            session.add(PriceRecord(
                service_id=service_id,
                plan_name=plan.plan_name,
                price=plan.price,
                currency=plan.currency,
                billing_period=plan.billing_period,
                features=json.dumps(plan.features, ensure_ascii=False),
                is_current=True,
                is_manual=is_manual,
                scraped_at=now,
            ))

        meta = session.get(ServiceMeta, service_id)
        if meta:
            meta.last_scraped_at = now
            meta.scrape_status = "ok"
            meta.last_error = ""

        session.commit()


def mark_scrape_error(service_id: str, error: str):
    with Session(get_engine()) as session:
        meta = session.get(ServiceMeta, service_id)
        if meta:
            meta.scrape_status = "error"
            meta.last_error = error[:500]
            meta.last_scraped_at = datetime.utcnow()
        session.commit()
