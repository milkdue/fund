from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.entities import MarketIndexDaily
from app.services.market_context_service import latest_market_context


def test_latest_market_context_from_local_rows():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    now = datetime.utcnow().replace(microsecond=0)
    with Session(engine) as db:
        db.add_all(
            [
                MarketIndexDaily(
                    index_code="HS300",
                    index_name="沪深300",
                    as_of=now,
                    close=3800,
                    daily_change_pct=0.5,
                    volatility_20d=1.2,
                    momentum_5d=1.8,
                ),
                MarketIndexDaily(
                    index_code="CSI500",
                    index_name="中证500",
                    as_of=now,
                    close=5600,
                    daily_change_pct=0.8,
                    volatility_20d=1.5,
                    momentum_5d=2.1,
                ),
                MarketIndexDaily(
                    index_code="CHINEXT",
                    index_name="创业板指",
                    as_of=now,
                    close=2100,
                    daily_change_pct=1.2,
                    volatility_20d=1.9,
                    momentum_5d=2.8,
                ),
            ]
        )
        db.commit()

        ctx = latest_market_context(db)
        assert ctx.data_freshness == "fresh"
        assert ctx.source_degraded is False
        assert ctx.market_score > 0
        assert ctx.style_score > 0


def test_latest_market_context_degraded_when_missing():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    old = datetime.utcnow().replace(microsecond=0) - timedelta(days=5)
    with Session(engine) as db:
        db.add(
            MarketIndexDaily(
                index_code="HS300",
                index_name="沪深300",
                as_of=old,
                close=3800,
                daily_change_pct=0.1,
                volatility_20d=1.2,
                momentum_5d=0.3,
            )
        )
        db.commit()

        ctx = latest_market_context(db)
        assert ctx.source_degraded is True
