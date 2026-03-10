from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import Base
from app.models.entities import AlertEvent, PredictionFeedback
from app.services.user_ops_service import track_user_event, weekly_user_report, write_api_audit


def test_user_ops_event_and_weekly_report():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)

    old_audit_enabled = settings.auth_audit_enabled
    settings.auth_audit_enabled = True
    try:
        with Session(engine) as db:
            ack1 = track_user_event(
                db,
                user_id="u1",
                event_name="watchlist_add",
                fund_code="110022",
                metadata={"source": "test"},
            )
            ack2 = track_user_event(
                db,
                user_id="u1",
                event_name="watchlist_add",
                fund_code="110022",
                metadata={"source": "test"},
            )

            write_api_audit(
                db,
                user_id="u1",
                endpoint="/v1/user/watchlist",
                method="POST",
                status_code=200,
                detail="ok",
            )
            db.add(
                PredictionFeedback(
                    user_id="u1",
                    fund_code="110022",
                    horizon="short",
                    is_helpful=1,
                    score=5,
                    comment="good",
                    pred_as_of=datetime.now(tz=UTC).replace(tzinfo=None),
                )
            )
            db.add(
                AlertEvent(
                    rule_id=1,
                    prediction_id=1,
                    user_id="u1",
                    fund_code="110022",
                    horizon="short",
                    message="hit",
                )
            )
            db.commit()

            report = weekly_user_report(db, user_id="u1")
    finally:
        settings.auth_audit_enabled = old_audit_enabled

    assert ack1["id"] == ack2["id"]
    assert ack2["count"] == 2
    assert report["audit_requests"] >= 1
    assert report["event_counts"].get("watchlist_add", 0) >= 2
