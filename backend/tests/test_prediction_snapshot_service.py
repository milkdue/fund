from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.services.prediction_snapshot_service import latest_snapshot, upsert_prediction_snapshot


def test_upsert_and_latest_prediction_snapshot():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    now = datetime.now(tz=UTC).replace(tzinfo=None)

    with Session(engine) as db:
        row1 = upsert_prediction_snapshot(
            db,
            fund_code="110022",
            horizon="short",
            as_of=now,
            model_version="short-v0.1",
            data_source="eastmoney_pingzhongdata",
            feature_payload={"daily_change_pct": 1.2, "volatility_20d": 1.7},
        )
        db.commit()
        db.refresh(row1)

        row2 = upsert_prediction_snapshot(
            db,
            fund_code="110022",
            horizon="short",
            as_of=now,
            model_version="short-v0.2",
            data_source="eastmoney_pingzhongdata",
            feature_payload={"daily_change_pct": 1.4, "volatility_20d": 1.8},
        )
        db.commit()
        db.refresh(row2)

        latest = latest_snapshot(db, fund_code="110022", horizon="short")

    assert row1.id == row2.id
    assert row1.snapshot_id != ""
    assert latest is not None
    assert latest.model_version == "short-v0.2"
