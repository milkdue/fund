from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Fund, IntradayEstimate, ModelBacktestReport, NewsSignalDaily, Prediction, Quote, QuoteSourceMeta, Watchlist


def seed_data(db: Session) -> None:
    if db.scalar(select(Fund.code).limit(1)):
        return

    now = datetime.utcnow()
    db.add_all(
        [
            Fund(code="110022", name="易方达消费行业", category="偏股混合"),
            Fund(code="161725", name="招商中证白酒指数", category="指数"),
            Fund(code="005827", name="易方达蓝筹精选", category="偏股混合"),
        ]
    )

    db.add_all(
        [
            Quote(fund_code="110022", nav=4.213, daily_change_pct=0.82, volatility_20d=1.86, as_of=now),
            Quote(fund_code="161725", nav=1.776, daily_change_pct=-0.31, volatility_20d=2.55, as_of=now),
            Quote(fund_code="005827", nav=2.104, daily_change_pct=0.44, volatility_20d=1.63, as_of=now),
        ]
    )

    db.add_all(
        [
            Prediction(fund_code="110022", horizon="short", up_probability=0.62, expected_return_pct=1.8, confidence=0.71, as_of=now),
            Prediction(fund_code="110022", horizon="mid", up_probability=0.58, expected_return_pct=4.2, confidence=0.64, as_of=now),
            Prediction(fund_code="161725", horizon="short", up_probability=0.47, expected_return_pct=-0.6, confidence=0.67, as_of=now),
            Prediction(fund_code="161725", horizon="mid", up_probability=0.52, expected_return_pct=2.1, confidence=0.61, as_of=now),
            Prediction(fund_code="005827", horizon="short", up_probability=0.59, expected_return_pct=1.2, confidence=0.68, as_of=now),
            Prediction(fund_code="005827", horizon="mid", up_probability=0.56, expected_return_pct=3.4, confidence=0.62, as_of=now),
        ]
    )
    db.commit()


def search_funds(db: Session, q: str) -> list[Fund]:
    stmt = select(Fund)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where((Fund.code.like(pattern)) | (Fund.name.like(pattern)))
    return list(db.scalars(stmt.limit(20)))


def latest_quote(db: Session, code: str) -> Quote | None:
    stmt = select(Quote).where(Quote.fund_code == code).order_by(Quote.as_of.desc()).limit(1)
    return db.scalars(stmt).first()


def previous_quote(db: Session, code: str, before_as_of: datetime | None = None) -> Quote | None:
    stmt = select(Quote).where(Quote.fund_code == code)
    if before_as_of is not None:
        stmt = stmt.where(Quote.as_of < before_as_of)
    stmt = stmt.order_by(Quote.as_of.desc()).limit(1)
    return db.scalars(stmt).first()


def latest_intraday_estimate(db: Session, code: str) -> IntradayEstimate | None:
    stmt = select(IntradayEstimate).where(IntradayEstimate.fund_code == code).order_by(IntradayEstimate.as_of.desc()).limit(1)
    return db.scalars(stmt).first()


def quote_source_for_as_of(db: Session, code: str, as_of: datetime) -> str | None:
    stmt = (
        select(QuoteSourceMeta.source)
        .where(QuoteSourceMeta.fund_code == code, QuoteSourceMeta.as_of == as_of)
        .limit(1)
    )
    return db.scalar(stmt)


def latest_prediction(db: Session, code: str, horizon: str) -> Prediction | None:
    stmt = (
        select(Prediction)
        .where(Prediction.fund_code == code, Prediction.horizon == horizon)
        .order_by(Prediction.as_of.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def latest_news_signal(db: Session, code: str) -> NewsSignalDaily | None:
    stmt = (
        select(NewsSignalDaily)
        .where(NewsSignalDaily.fund_code == code)
        .order_by(NewsSignalDaily.trade_date.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def latest_backtest_report(db: Session, horizon: str) -> ModelBacktestReport | None:
    stmt = (
        select(ModelBacktestReport)
        .where(ModelBacktestReport.horizon == horizon)
        .order_by(ModelBacktestReport.report_date.desc(), ModelBacktestReport.generated_at.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def get_watchlist(db: Session, user_id: str) -> list[Watchlist]:
    return list(db.scalars(select(Watchlist).where(Watchlist.user_id == user_id)))


def add_watchlist(db: Session, user_id: str, fund_code: str) -> Watchlist:
    existing = db.scalar(select(Watchlist).where(Watchlist.user_id == user_id, Watchlist.fund_code == fund_code))
    if existing:
        return existing
    item = Watchlist(user_id=user_id, fund_code=fund_code)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


def mock_last_train_at() -> datetime:
    return datetime.utcnow() - timedelta(hours=6)
