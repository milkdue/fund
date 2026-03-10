from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Fund(Base):
    __tablename__ = "funds"

    code: Mapped[str] = mapped_column(String(16), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)


class Quote(Base):
    __tablename__ = "quotes"
    __table_args__ = (UniqueConstraint("fund_code", "as_of", name="uq_quote_fund_as_of"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    nav: Mapped[float] = mapped_column(Float, nullable=False)
    daily_change_pct: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_20d: Mapped[float] = mapped_column(Float, nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


class Prediction(Base):
    __tablename__ = "predictions"
    __table_args__ = (UniqueConstraint("fund_code", "horizon", "as_of", name="uq_pred_fund_horizon_as_of"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    horizon: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    up_probability: Mapped[float] = mapped_column(Float, nullable=False)
    expected_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)


class Watchlist(Base):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("user_id", "fund_code", name="uq_watchlist_user_fund"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class NewsRaw(Base):
    __tablename__ = "news_raw"
    __table_args__ = (UniqueConstraint("fund_code", "title_hash", "published_at", name="uq_news_raw_fund_hash_pub"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    title_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    event_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class NewsSignalDaily(Base):
    __tablename__ = "news_signal_daily"
    __table_args__ = (UniqueConstraint("fund_code", "trade_date", name="uq_news_signal_fund_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    headline_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    sentiment_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    event_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    volume_shock: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_title: Mapped[str] = mapped_column(String(256), nullable=False, default="暂无新增公告/舆情")
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class ModelBacktestReport(Base):
    __tablename__ = "model_backtest_reports"
    __table_args__ = (UniqueConstraint("horizon", "report_date", name="uq_backtest_horizon_report_date"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    horizon: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    report_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=180)
    model_version: Mapped[str] = mapped_column(String(64), nullable=False, default="unknown")
    accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    auc: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    precision: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    recall: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    f1: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    annualized_return: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_drawdown: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sharpe: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class MarketIndexDaily(Base):
    __tablename__ = "market_index_daily"
    __table_args__ = (UniqueConstraint("index_code", "as_of", name="uq_market_index_code_as_of"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    index_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    index_name: Mapped[str] = mapped_column(String(64), nullable=False)
    as_of: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    daily_change_pct: Mapped[float] = mapped_column(Float, nullable=False)
    volatility_20d: Mapped[float] = mapped_column(Float, nullable=False)
    momentum_5d: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class PredictionFeedback(Base):
    __tablename__ = "prediction_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    horizon: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    is_helpful: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    comment: Mapped[str | None] = mapped_column(String(512), nullable=True)
    pred_as_of: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class AlertRule(Base):
    __tablename__ = "alert_rules"
    __table_args__ = (UniqueConstraint("user_id", "fund_code", "horizon", name="uq_alert_rule_user_fund_horizon"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    horizon: Mapped[str] = mapped_column(String(16), nullable=False, default="short", index=True)
    min_up_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.6)
    min_confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.55)
    min_expected_return_pct: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    enabled: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


class AlertEvent(Base):
    __tablename__ = "alert_events"
    __table_args__ = (UniqueConstraint("rule_id", "prediction_id", name="uq_alert_event_rule_prediction"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rule_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    prediction_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    horizon: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    message: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)


class PredictionABResult(Base):
    __tablename__ = "prediction_ab_results"
    __table_args__ = (UniqueConstraint("fund_code", "horizon", "as_of", "candidate_model_version", name="uq_ab_fund_horizon_as_of_candidate"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    horizon: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    as_of: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    baseline_model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    candidate_model_version: Mapped[str] = mapped_column(String(64), nullable=False)
    baseline_up_probability: Mapped[float] = mapped_column(Float, nullable=False)
    candidate_up_probability: Mapped[float] = mapped_column(Float, nullable=False)
    baseline_expected_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    candidate_expected_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    actual_return_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    winner: Mapped[str] = mapped_column(String(16), nullable=False, default="tie")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class AiJudgementCache(Base):
    __tablename__ = "ai_judgement_cache"
    __table_args__ = (
        UniqueConstraint("fund_code", "horizon", "as_of", "model", "prompt_version", name="uq_ai_judgement_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fund_code: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    horizon: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    as_of: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    data_freshness: Mapped[str] = mapped_column(String(16), nullable=False, default="fresh")
    provider: Mapped[str] = mapped_column(String(32), nullable=False, default="fallback-rule")
    model: Mapped[str] = mapped_column(String(64), nullable=False, default="fallback")
    prompt_version: Mapped[str] = mapped_column(String(16), nullable=False, default="v1")
    trend: Mapped[str] = mapped_column(String(16), nullable=False, default="sideways")
    trend_strength: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    agreement_with_model: Mapped[str] = mapped_column(String(16), nullable=False, default="agree")
    key_reasons_json: Mapped[str] = mapped_column(String(2048), nullable=False, default="[]")
    risk_warnings_json: Mapped[str] = mapped_column(String(2048), nullable=False, default="[]")
    confidence_adjustment: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    adjusted_up_probability: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    summary: Mapped[str] = mapped_column(String(1024), nullable=False, default="")
    raw_response: Mapped[str | None] = mapped_column(String(8192), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
