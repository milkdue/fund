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
    model_version: str = "unknown"
    data_source: str = "eastmoney"
    snapshot_id: str | None = None


class ExplainFactor(BaseModel):
    name: str
    contribution: float


class ExplainResponse(BaseModel):
    code: str
    horizon: str
    data_freshness: str = "fresh"
    confidence_interval_pct: tuple[float, float]
    top_factors: list[ExplainFactor]
    risk_flags: list[str] = Field(default_factory=list)


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


class AlertEventItem(BaseModel):
    id: int
    fund_code: str
    horizon: str
    message: str
    created_at: datetime


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


class DataHealthResponse(BaseModel):
    generated_at: datetime
    fund_pool_size: int = Field(ge=0)
    quote_coverage_48h: float = Field(ge=0.0, le=1.0)
    prediction_coverage_48h: float = Field(ge=0.0, le=1.0)
    latest_quote_at: datetime | None = None
    latest_prediction_at: datetime | None = None
    latest_news_trade_date: str | None = None
    latest_market_at: datetime | None = None
    quote_freshness: str
    prediction_freshness: str
    market_freshness: str
    source_status: dict[str, str]


class PredictionChangeFactor(BaseModel):
    name: str
    before: float | None = None
    after: float | None = None
    delta: float


class PredictionChangeResponse(BaseModel):
    code: str
    horizon: str
    current_as_of: datetime
    previous_as_of: datetime | None = None
    data_freshness: str = "fresh"
    up_probability_delta: float
    expected_return_pct_delta: float
    confidence_delta: float
    changed_factors: list[PredictionChangeFactor] = Field(default_factory=list)
    summary: str


class WatchlistInsightItem(BaseModel):
    fund_code: str
    short_up_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    short_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    mid_up_probability: float | None = Field(default=None, ge=0.0, le=1.0)
    mid_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    data_freshness: str = "stale"
    risk_level: str
    signal: str


class WatchlistInsightsResponse(BaseModel):
    user_id: str
    generated_at: datetime
    items: list[WatchlistInsightItem] = Field(default_factory=list)


class UserEventIn(BaseModel):
    event_name: str = Field(min_length=2, max_length=64)
    fund_code: str | None = Field(default=None, max_length=16)
    metadata: dict[str, str | int | float | bool] | None = None


class UserEventResponse(BaseModel):
    id: int
    count: int = Field(ge=1)
    event_day: str


class WeeklyReportResponse(BaseModel):
    user_id: str
    from_date: str
    to_date: str
    audit_requests: int = Field(ge=0)
    event_counts: dict[str, int]
    feedback_total: int = Field(ge=0)
    feedback_helpful_rate: float = Field(ge=0.0, le=1.0)
    alert_hits: int = Field(ge=0)


class WalkForwardWindowMetrics(BaseModel):
    window_start: str
    window_end: str
    sample_size: int = Field(ge=0)
    accuracy: float = Field(ge=0.0, le=1.0)
    auc: float = Field(ge=0.0, le=1.0)
    f1: float = Field(ge=0.0, le=1.0)
    annualized_return: float
    max_drawdown: float
    sharpe: float


class WalkForwardBacktestResponse(BaseModel):
    horizon: str
    generated_at: datetime
    window_days: int = Field(ge=30)
    step_days: int = Field(ge=7)
    window_count: int = Field(ge=0)
    avg_accuracy: float = Field(ge=0.0, le=1.0)
    avg_auc: float = Field(ge=0.0, le=1.0)
    avg_f1: float = Field(ge=0.0, le=1.0)
    avg_annualized_return: float
    worst_max_drawdown: float
    avg_sharpe: float
    windows: list[WalkForwardWindowMetrics] = Field(default_factory=list)


class DataSourceItem(BaseModel):
    name: str
    purpose: str
    url: str


class DataSourceResponse(BaseModel):
    sources: list[DataSourceItem]
