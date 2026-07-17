from datetime import datetime
from typing import List, Optional
from sqlmodel import Field, SQLModel
from pydantic import BaseModel


# ── DB tables ──────────────────────────────────────────────────────────────


class PriceRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    service_id: str = Field(index=True)
    plan_name: str
    price: float
    currency: str = "ARS"
    billing_period: str = "monthly"
    features: str = ""  # JSON-encoded list
    is_current: bool = Field(default=True, index=True)
    is_manual: bool = False
    scraped_at: datetime = Field(default_factory=datetime.utcnow)


class ServiceMeta(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    category: str = ""
    website_url: str
    pricing_url: str
    logo_url: str = ""
    last_scraped_at: Optional[datetime] = None
    scrape_status: str = "pending"   # ok | error | pending
    last_error: str = ""


# ── API response schemas ───────────────────────────────────────────────────


class PlanOut(BaseModel):
    plan_name: str
    price: float
    currency: str
    billing_period: str
    features: List[str]
    is_manual: bool
    scraped_at: datetime


class ServiceOut(BaseModel):
    id: str
    name: str
    category: str
    website_url: str
    logo_url: str
    last_scraped_at: Optional[datetime]
    scrape_status: str
    plans: List[PlanOut]


class PricesResponse(BaseModel):
    generated_at: datetime
    services: List[ServiceOut]


class ManualPriceIn(BaseModel):
    plan_name: str
    price: float
    currency: str = "ARS"
    billing_period: str = "monthly"
    features: List[str] = []


class ScrapeResult(BaseModel):
    service_id: str
    status: str
    plans_saved: int
    error: Optional[str] = None
