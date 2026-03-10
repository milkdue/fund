from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.entities import Prediction, Quote
from app.services.walkforward_service import build_walkforward_report


def test_walkforward_report_with_sample_data():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    now = datetime.now(tz=UTC).replace(tzinfo=None)

    with Session(engine) as db:
        for idx in range(90):
            as_of = now - timedelta(days=idx)
            change = 0.7 if idx % 3 != 0 else -0.6
            expected = 1.0 if idx % 3 != 0 else -0.8
            prob = 0.64 if expected > 0 else 0.34
            db.add(
                Quote(
                    fund_code="110022",
                    nav=4.0 + idx * 0.005,
                    daily_change_pct=change,
                    volatility_20d=1.9,
                    as_of=as_of,
                )
            )
            db.add(
                Prediction(
                    fund_code="110022",
                    horizon="short",
                    up_probability=prob,
                    expected_return_pct=expected,
                    confidence=0.69,
                    as_of=as_of,
                )
            )
        db.commit()

        report = build_walkforward_report(
            db,
            horizon="short",
            window_days=45,
            step_days=10,
            max_windows=6,
        )

    assert report["horizon"] == "short"
    assert report["window_count"] >= 1
    assert len(report["windows"]) == report["window_count"]
    assert 0.0 <= report["avg_accuracy"] <= 1.0
