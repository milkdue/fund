from datetime import UTC, date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.entities import Fund, MarketIndexDaily, NewsSignalDaily, Prediction, Quote
from app.services.data_health_service import build_data_health_summary


def test_build_data_health_summary():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    now = datetime.now(tz=UTC).replace(tzinfo=None)

    with Session(engine) as db:
        db.add_all(
            [
                Fund(code="110022", name="易方达消费行业", category="偏股混合"),
                Fund(code="161725", name="招商中证白酒指数", category="指数"),
            ]
        )
        db.add(
            Quote(
                fund_code="110022",
                nav=4.2,
                daily_change_pct=1.1,
                volatility_20d=1.7,
                as_of=now,
            )
        )
        db.add(
            Prediction(
                fund_code="110022",
                horizon="short",
                up_probability=0.61,
                expected_return_pct=1.3,
                confidence=0.68,
                as_of=now,
            )
        )
        db.add(
            NewsSignalDaily(
                fund_code="110022",
                trade_date=date.today(),
                headline_count=2,
                sentiment_score=0.1,
                event_score=0.2,
                volume_shock=0.1,
                sample_title="公告更新",
            )
        )
        db.add(
            MarketIndexDaily(
                index_code="HS300",
                index_name="沪深300",
                as_of=now,
                close=3500,
                daily_change_pct=0.3,
                volatility_20d=1.2,
                momentum_5d=0.5,
            )
        )
        db.commit()

        summary = build_data_health_summary(db)

    assert summary["fund_pool_size"] == 2
    assert 0.0 <= summary["quote_coverage_48h"] <= 1.0
    assert 0.0 <= summary["prediction_coverage_48h"] <= 1.0
    assert summary["source_status"]["eastmoney_nav"] in {"ok", "degraded"}
