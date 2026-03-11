from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Fund, MarketIndexDaily, NewsSignalDaily, Prediction, Quote
from app.services.time_utils import shanghai_now_naive


def _freshness_label(as_of: datetime | None) -> str:
    if as_of is None:
        return "stale"
    delta_hours = (shanghai_now_naive() - as_of).total_seconds() / 3600
    if delta_hours <= 36:
        return "fresh"
    if delta_hours <= 72:
        return "lagging"
    return "stale"


def build_data_health_summary(db: Session) -> dict:
    now = shanghai_now_naive()
    fund_total = int(db.scalar(select(func.count(Fund.code))) or 0)

    latest_quote_ts = db.scalar(select(func.max(Quote.as_of)))
    latest_prediction_ts = db.scalar(select(func.max(Prediction.as_of)))
    latest_news_day = db.scalar(select(func.max(NewsSignalDaily.trade_date)))
    latest_market_ts = db.scalar(select(func.max(MarketIndexDaily.as_of)))

    recent_cutoff = now - timedelta(hours=48)
    quote_recent_funds = int(
        db.scalar(
            select(func.count(func.distinct(Quote.fund_code))).where(Quote.as_of >= recent_cutoff)
        )
        or 0
    )
    pred_recent_funds = int(
        db.scalar(
            select(func.count(func.distinct(Prediction.fund_code))).where(Prediction.as_of >= recent_cutoff)
        )
        or 0
    )

    quote_coverage = round((quote_recent_funds / fund_total), 4) if fund_total else 0.0
    pred_coverage = round((pred_recent_funds / fund_total), 4) if fund_total else 0.0

    return {
        "generated_at": now,
        "fund_pool_size": fund_total,
        "quote_coverage_48h": quote_coverage,
        "prediction_coverage_48h": pred_coverage,
        "latest_quote_at": latest_quote_ts,
        "latest_prediction_at": latest_prediction_ts,
        "latest_news_trade_date": latest_news_day.isoformat() if latest_news_day else None,
        "latest_market_at": latest_market_ts,
        "quote_freshness": _freshness_label(latest_quote_ts),
        "prediction_freshness": _freshness_label(latest_prediction_ts),
        "market_freshness": _freshness_label(latest_market_ts),
        "source_status": {
            "eastmoney_nav": "ok" if latest_quote_ts else "degraded",
            "eastmoney_news": "ok" if latest_news_day else "degraded",
            "eastmoney_market": "ok" if latest_market_ts else "degraded",
        },
    }
