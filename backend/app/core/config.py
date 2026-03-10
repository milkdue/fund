from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Fund Predictor API"
    env: str = "dev"
    db_url: str = "sqlite:///./fund_predictor.db"
    redis_url: str = "redis://localhost:6379/0"
    auto_create_tables: bool = True
    bootstrap_demo_data: bool = False
    cron_secret: str | None = None
    auth_enabled: bool = False
    auth_bearer_token: str | None = None
    auth_token_map: str | None = None
    auth_default_user_id: str = "authorized-user"
    auth_user_api_limit_per_min: int = 120
    auth_audit_enabled: bool = True
    source_nav_limit_per_min: int = 90
    source_search_limit_per_min: int = 30
    source_news_limit_per_min: int = 20
    source_market_limit_per_min: int = 30

    model_short_version: str = "short-v0.1"
    model_mid_version: str = "mid-v0.1"
    model_candidate_short_version: str = "short-v0.2"
    model_candidate_mid_version: str = "mid-v0.2"
    model_ab_enabled: bool = True
    gemini_enabled: bool = False
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.0-flash"
    gemini_temperature: float = 0.2
    gemini_timeout_ms: int = 12000
    gemini_max_output_tokens: int = 512
    gemini_prompt_version: str = "v1"
    gemini_daily_budget_calls: int = 400
    gemini_compliance_filter_enabled: bool = True
    bark_enabled: bool = False
    bark_base_url: str = "https://api.day.app"
    bark_user_key: str | None = None
    bark_icon_url: str | None = None
    bark_group: str = "fund_predictor"
    bark_limit_per_min: int = 30
    bark_timeout_ms: int = 5000

    model_config = SettingsConfigDict(env_prefix="FUND_", env_file=".env", extra="ignore")


settings = Settings()
