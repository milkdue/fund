from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.entities import Prediction, Quote
from app.services.backtest_service import generate_backtest_report


def test_generate_backtest_report_with_sample_data():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    now = datetime.now(tz=UTC).replace(tzinfo=None)
    with Session(engine) as db:
        for idx in range(12):
            as_of = now - timedelta(days=idx)
            change = 0.8 if idx % 2 == 0 else -0.6
            prob = 0.65 if idx % 2 == 0 else 0.35
            expected = 1.2 if idx % 2 == 0 else -0.9
            db.add(
                Quote(
                    fund_code="110022",
                    nav=4.0 + idx * 0.01,
                    daily_change_pct=change,
                    volatility_20d=1.8,
                    as_of=as_of,
                )
            )
            db.add(
                Prediction(
                    fund_code="110022",
                    horizon="short",
                    up_probability=prob,
                    expected_return_pct=expected,
                    confidence=0.7,
                    as_of=as_of,
                )
            )
        db.commit()

        report = generate_backtest_report(db, horizon="short", window_days=30)
        assert report.sample_size == 12
        assert 0.0 <= report.accuracy <= 1.0
        assert 0.0 <= report.auc <= 1.0
        assert 0.0 <= report.f1 <= 1.0
