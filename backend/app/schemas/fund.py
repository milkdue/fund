from datetime import datetime

from pydantic import BaseModel, Field


class FundItem(BaseModel):
    code: str
    name: str
    category: str


class QuoteResponse(BaseModel):
    code: str
    as_of: datetime
    nav: float
    daily_change_pct: float
    volatility_20d: float


class PredictResponse(BaseModel):
    code: str
    horizon: str
    as_of: datetime
    up_probability: float = Field(ge=0.0, le=1.0)
    expected_return_pct: float
    confidence: float = Field(ge=0.0, le=1.0)


class ExplainFactor(BaseModel):
    name: str
    contribution: float


class ExplainResponse(BaseModel):
    code: str
    horizon: str
    confidence_interval_pct: tuple[float, float]
    top_factors: list[ExplainFactor]


class WatchlistIn(BaseModel):
    fund_code: str


class WatchlistItem(BaseModel):
    user_id: str
    fund_code: str


class ModelHealthResponse(BaseModel):
    short_model_version: str
    mid_model_version: str
    last_train_at: datetime
    coverage_rate: float = Field(ge=0.0, le=1.0)


class DataSourceItem(BaseModel):
    name: str
    purpose: str
    url: str


class DataSourceResponse(BaseModel):
    sources: list[DataSourceItem]
