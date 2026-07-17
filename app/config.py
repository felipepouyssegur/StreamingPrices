from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "sqlite:///./streaming_prices.db"
    api_key: str = "change-me-in-production"
    scrape_interval_hours: int = 24
    headless: bool = True
    scrape_enabled: bool = True

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
