from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fund Predictor API"
    env: str = "dev"
    db_url: str = "sqlite:///./fund_predictor.db"
    redis_url: str = "redis://localhost:6379/0"
    auto_create_tables: bool = True
    bootstrap_demo_data: bool = False
    cron_secret: str | None = None
    source_nav_limit_per_min: int = 90
    source_search_limit_per_min: int = 30
    source_news_limit_per_min: int = 20

    model_short_version: str = "short-v0.1"
    model_mid_version: str = "mid-v0.1"

    model_config = SettingsConfigDict(env_prefix="FUND_", env_file=".env", extra="ignore")


settings = Settings()
