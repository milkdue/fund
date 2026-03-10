from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Fund, NewsSignalDaily, Prediction, Quote
from app.services.market_context_service import get_or_refresh_market_context
from app.services.fund_data_source import FundDataError, FundDataRateLimitError, fetch_latest_snapshot
from app.services.alerts_service import evaluate_and_record_alert_events
from app.services.prediction_ab_service import upsert_ab_result
from app.services.predictor import candidate_rule_predictions, rule_based_predictions
from app.core.config import settings


class MarketSyncError(Exception):
    pass


class MarketSyncRateLimitError(MarketSyncError):
    pass


def refresh_fund_data(db: Session, code: str) -> Quote:
    try:
        snapshot = fetch_latest_snapshot(code)
    except FundDataRateLimitError as exc:
        raise MarketSyncRateLimitError(str(exc)) from exc
    except FundDataError as exc:
        raise MarketSyncError(str(exc)) from exc

    fund = db.scalar(select(Fund).where(Fund.code == code))
    if not fund:
        fund = Fund(code=code, name=snapshot.name, category="未分类")
        db.add(fund)
    elif fund.name != snapshot.name:
        fund.name = snapshot.name

    existing_quote = db.scalar(select(Quote).where(Quote.fund_code == code, Quote.as_of == snapshot.as_of))
    if not existing_quote:
        existing_quote = Quote(
            fund_code=code,
            nav=snapshot.nav,
            daily_change_pct=snapshot.daily_change_pct,
            volatility_20d=snapshot.volatility_20d,
            as_of=snapshot.as_of,
        )
        db.add(existing_quote)
    else:
        existing_quote.nav = snapshot.nav
        existing_quote.daily_change_pct = snapshot.daily_change_pct
        existing_quote.volatility_20d = snapshot.volatility_20d

    news_signal = db.scalar(
        select(NewsSignalDaily)
        .where(NewsSignalDaily.fund_code == code)
        .order_by(NewsSignalDaily.trade_date.desc())
        .limit(1)
    )
    market_ctx = get_or_refresh_market_context(db)
    sentiment_score = news_signal.sentiment_score if news_signal else 0.0
    event_score = news_signal.event_score if news_signal else 0.0
    volume_shock_score = news_signal.volume_shock if news_signal else 0.0

    pred_values = rule_based_predictions(
        snapshot.daily_change_pct,
        snapshot.volatility_20d,
        sentiment_score=sentiment_score,
        event_score=event_score,
        volume_shock_score=volume_shock_score,
        market_score=market_ctx.market_score,
        style_score=market_ctx.style_score,
        market_degraded=market_ctx.source_degraded,
    )
    cand_values = candidate_rule_predictions(
        snapshot.daily_change_pct,
        snapshot.volatility_20d,
        sentiment_score=sentiment_score,
        event_score=event_score,
        volume_shock_score=volume_shock_score,
        market_score=market_ctx.market_score,
        style_score=market_ctx.style_score,
        market_degraded=market_ctx.source_degraded,
    )
    as_of = snapshot.as_of
    for horizon, payload in pred_values.items():
        row = db.scalar(select(Prediction).where(Prediction.fund_code == code, Prediction.horizon == horizon, Prediction.as_of == as_of))
        if not row:
            row = Prediction(
                fund_code=code,
                horizon=horizon,
                up_probability=payload["up_probability"],
                expected_return_pct=payload["expected_return_pct"],
                confidence=payload["confidence"],
                as_of=as_of,
            )
            db.add(row)
        else:
            row.up_probability = payload["up_probability"]
            row.expected_return_pct = payload["expected_return_pct"]
            row.confidence = payload["confidence"]

        db.flush()

        if settings.model_ab_enabled:
            candidate = cand_values.get(horizon, payload)
            upsert_ab_result(
                db,
                fund_code=code,
                horizon=horizon,
                as_of=as_of,
                baseline_up_probability=payload["up_probability"],
                baseline_expected_return_pct=payload["expected_return_pct"],
                candidate_up_probability=candidate["up_probability"],
                candidate_expected_return_pct=candidate["expected_return_pct"],
                actual_return_pct=snapshot.daily_change_pct,
            )
        evaluate_and_record_alert_events(
            db,
            fund_code=code,
            horizon=horizon,
            prediction_id=row.id,
        )

    db.commit()
    return existing_quote
