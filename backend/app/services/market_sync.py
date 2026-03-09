from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Fund, Prediction, Quote
from app.services.fund_data_source import FundDataError, FundDataRateLimitError, fetch_latest_snapshot
from app.services.predictor import rule_based_predictions


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

    pred_values = rule_based_predictions(snapshot.daily_change_pct, snapshot.volatility_20d)
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

    db.commit()
    return existing_quote
