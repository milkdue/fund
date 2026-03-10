from datetime import datetime

from pydantic import BaseModel, Field


class FundItem(BaseModel):
    code: str
    name: str
    category: str


class QuoteResponse(BaseModel):
    code: str
    as_of: datetime
    data_freshness: str = "fresh"
    nav: float
    daily_change_pct: float
    volatility_20d: float


class PredictResponse(BaseModel):
    code: str
    horizon: str
    as_of: datetime
    data_freshness: str = "fresh"
    up_probability: float = Field(ge=0.0, le=1.0)
    expected_return_pct: float
    confidence: float = Field(ge=0.0, le=1.0)


class ExplainFactor(BaseModel):
    name: str
    contribution: float


class ExplainResponse(BaseModel):
    code: str
    horizon: str
    data_freshness: str = "fresh"
    confidence_interval_pct: tuple[float, float]
    top_factors: list[ExplainFactor]
    risk_flags: list[str] = []


class KlineItem(BaseModel):
    ts: datetime
    open: float
    high: float
    low: float
    close: float


class KlineResponse(BaseModel):
    code: str
    is_synthetic: bool = True
    note: str = "derived_from_nav_estimation_not_true_ohlc"
    items: list[KlineItem]


class NewsSignalResponse(BaseModel):
    code: str
    trade_date: str
    headline_count: int
    sentiment_score: float
    event_score: float
    volume_shock: float
    sample_title: str


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


class BacktestMetrics(BaseModel):
    accuracy: float = Field(ge=0.0, le=1.0)
    auc: float = Field(ge=0.0, le=1.0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)
    annualized_return: float
    max_drawdown: float
    sharpe: float
    sample_size: int = Field(ge=0)


class BacktestReportResponse(BaseModel):
    horizon: str
    generated_at: datetime
    report_date: str
    window_days: int
    model_version: str
    metrics: BacktestMetrics


class FeedbackIn(BaseModel):
    horizon: str = Field(pattern="^(short|mid)$")
    is_helpful: bool
    score: int = Field(default=3, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=512)


class FeedbackItem(BaseModel):
    id: int
    user_id: str
    fund_code: str
    horizon: str
    is_helpful: bool
    score: int
    comment: str | None
    pred_as_of: datetime | None
    created_at: datetime


class FeedbackSummaryResponse(BaseModel):
    fund_code: str
    horizon: str
    total: int
    helpful: int
    helpful_rate: float
    avg_score: float


class AlertRuleIn(BaseModel):
    fund_code: str
    horizon: str = Field(pattern="^(short|mid)$")
    min_up_probability: float = Field(default=0.6, ge=0.0, le=1.0)
    min_confidence: float = Field(default=0.55, ge=0.0, le=1.0)
    min_expected_return_pct: float = 0.0
    enabled: bool = True


class AlertRuleItem(BaseModel):
    id: int
    user_id: str
    fund_code: str
    horizon: str
    min_up_probability: float
    min_confidence: float
    min_expected_return_pct: float
    enabled: bool
    updated_at: datetime


class AlertHitItem(BaseModel):
    rule_id: int
    fund_code: str
    horizon: str
    up_probability: float
    confidence: float
    expected_return_pct: float
    as_of: datetime
    message: str


class AlertCheckResponse(BaseModel):
    user_id: str
    hit_count: int
    items: list[AlertHitItem]


class AbCompareItem(BaseModel):
    fund_code: str
    horizon: str
    as_of: datetime
    baseline_model_version: str
    candidate_model_version: str
    baseline_up_probability: float
    candidate_up_probability: float
    baseline_expected_return_pct: float
    candidate_expected_return_pct: float
    actual_return_pct: float | None
    winner: str


class AbSummaryResponse(BaseModel):
    horizon: str
    baseline_model_version: str
    candidate_model_version: str
    sample_size: int
    candidate_win_rate: float
    baseline_win_rate: float
    tie_rate: float


class MarketContextResponse(BaseModel):
    market_score: float
    style_score: float
    data_freshness: str
    source_degraded: bool


class AiJudgementResponse(BaseModel):
    code: str
    horizon: str
    as_of: datetime
    data_freshness: str
    trend: str
    trend_strength: int = Field(ge=0, le=100)
    agreement_with_model: str
    key_reasons: list[str]
    risk_warnings: list[str]
    confidence_adjustment: float
    adjusted_up_probability: float = Field(ge=0.0, le=1.0)
    summary: str
    provider: str
    model: str


class DataSourceItem(BaseModel):
    name: str
    purpose: str
    url: str


class DataSourceResponse(BaseModel):
    sources: list[DataSourceItem]
