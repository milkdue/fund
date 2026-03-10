from datetime import UTC, date, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.session import Base
from app.models.entities import AiJudgementCache, Fund, MarketIndexDaily, ModelBacktestReport, NewsSignalDaily, Prediction, Quote
from app.services.ai_second_opinion import get_ai_second_opinion


def _prepare_db() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    db = sessionmaker(bind=engine, autoflush=False, autocommit=False)()

    now = datetime.now(tz=UTC).replace(tzinfo=None)
    db.add(Fund(code="110022", name="易方达消费行业", category="偏股混合"))
    db.add(Quote(fund_code="110022", nav=4.22, daily_change_pct=0.86, volatility_20d=1.92, as_of=now))
    db.add(Prediction(fund_code="110022", horizon="short", up_probability=0.63, expected_return_pct=1.7, confidence=0.74, as_of=now))
    db.add(NewsSignalDaily(fund_code="110022", trade_date=date.today(), headline_count=4, sentiment_score=0.25, event_score=0.2, volume_shock=0.1, sample_title="基金公告更新"))
    db.add(ModelBacktestReport(horizon="short", report_date=date.today(), model_version="short-v0.1", accuracy=0.58, auc=0.6, precision=0.57, recall=0.55, f1=0.56, annualized_return=0.08, max_drawdown=-0.13, sharpe=0.72, sample_size=500))
    db.add_all(
        [
            MarketIndexDaily(index_code="HS300", index_name="沪深300", as_of=now, close=3500, daily_change_pct=0.3, volatility_20d=1.2, momentum_5d=0.6),
            MarketIndexDaily(index_code="CSI500", index_name="中证500", as_of=now, close=5800, daily_change_pct=0.2, volatility_20d=1.3, momentum_5d=0.5),
            MarketIndexDaily(index_code="CHINEXT", index_name="创业板", as_of=now, close=2100, daily_change_pct=0.4, volatility_20d=1.5, momentum_5d=0.7),
        ]
    )
    db.commit()
    return db


def test_ai_second_opinion_fallback_and_cache():
    db = _prepare_db()
    old_enabled = settings.gemini_enabled
    old_key = settings.gemini_api_key
    old_model = settings.gemini_model
    old_prompt_version = settings.gemini_prompt_version

    settings.gemini_enabled = False
    settings.gemini_api_key = None
    settings.gemini_model = "gemini-2.0-flash"
    settings.gemini_prompt_version = "v1"

    try:
        first = get_ai_second_opinion(db, code="110022", horizon="short")
        second = get_ai_second_opinion(db, code="110022", horizon="short")
        cache_rows = db.scalars(select(AiJudgementCache)).all()
    finally:
        settings.gemini_enabled = old_enabled
        settings.gemini_api_key = old_key
        settings.gemini_model = old_model
        settings.gemini_prompt_version = old_prompt_version
        db.close()

    assert first["provider"] == "fallback-rule"
    assert first["model"] == "fallback"
    assert first["trend"] in {"up", "down", "sideways"}
    assert 0.0 <= first["adjusted_up_probability"] <= 1.0
    assert first["key_reasons"]

    assert first == second

    assert len(cache_rows) == 1


def test_ai_second_opinion_budget_fallback():
    db = _prepare_db()
    old_enabled = settings.gemini_enabled
    old_key = settings.gemini_api_key
    old_model = settings.gemini_model
    old_budget = settings.gemini_daily_budget_calls

    settings.gemini_enabled = True
    settings.gemini_api_key = "dummy-key"
    settings.gemini_model = "gemini-2.0-flash"
    settings.gemini_daily_budget_calls = 0

    try:
        payload = get_ai_second_opinion(db, code="110022", horizon="short")
    finally:
        settings.gemini_enabled = old_enabled
        settings.gemini_api_key = old_key
        settings.gemini_model = old_model
        settings.gemini_daily_budget_calls = old_budget
        db.close()

    assert payload["provider"] == "gemini-fallback"
    assert "预算" in payload["summary"]


def test_ai_second_opinion_compliance_filter(monkeypatch):
    db = _prepare_db()
    old_enabled = settings.gemini_enabled
    old_key = settings.gemini_api_key
    old_model = settings.gemini_model
    old_budget = settings.gemini_daily_budget_calls
    old_filter = settings.gemini_compliance_filter_enabled

    settings.gemini_enabled = True
    settings.gemini_api_key = "dummy-key"
    settings.gemini_model = "gemini-2.0-flash"
    settings.gemini_daily_budget_calls = 10
    settings.gemini_compliance_filter_enabled = True

    def _mock_call_gemini(_context):
        return (
            {
                "trend": "up",
                "trend_strength": 88,
                "agreement_with_model": "agree",
                "key_reasons": ["这只基金必涨，稳赚机会"],
                "risk_warnings": ["几乎无风险，建议重仓"],
                "confidence_adjustment": 0.1,
                "adjusted_up_probability": 0.8,
                "summary": "该基金必涨且保本。",
            },
            '{"trend":"up"}',
        )

    monkeypatch.setattr("app.services.ai_second_opinion._call_gemini", _mock_call_gemini)
    try:
        payload = get_ai_second_opinion(db, code="110022", horizon="short")
    finally:
        settings.gemini_enabled = old_enabled
        settings.gemini_api_key = old_key
        settings.gemini_model = old_model
        settings.gemini_daily_budget_calls = old_budget
        settings.gemini_compliance_filter_enabled = old_filter
        db.close()

    assert payload["provider"] == "gemini"
    assert "必涨" not in payload["summary"]
    assert any("降级" in item for item in payload["risk_warnings"])
