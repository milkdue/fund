from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.entities import Prediction
from app.services.alerts_service import check_user_alerts, evaluate_and_record_alert_events, upsert_alert_rule
from app.services.feedback_service import add_feedback, feedback_summary
from app.services.model_ab_service import ab_summary, list_latest_ab_results
from app.services.prediction_ab_service import upsert_ab_result


def _build_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return engine


def test_feedback_summary_flow():
    engine = _build_db()
    with Session(engine) as db:
        now = datetime.now(tz=UTC).replace(tzinfo=None)
        db.add(
            Prediction(
                fund_code="110022",
                horizon="short",
                up_probability=0.62,
                expected_return_pct=1.3,
                confidence=0.7,
                as_of=now,
            )
        )
        db.commit()

        add_feedback(
            db,
            user_id="u1",
            fund_code="110022",
            horizon="short",
            is_helpful=True,
            score=5,
            comment="ok",
        )
        add_feedback(
            db,
            user_id="u2",
            fund_code="110022",
            horizon="short",
            is_helpful=False,
            score=2,
            comment="not good",
        )
        summary = feedback_summary(db, fund_code="110022", horizon="short")
        assert summary["total"] == 2
        assert summary["helpful"] == 1
        assert 0.0 <= summary["helpful_rate"] <= 1.0


def test_alert_rule_and_check_flow():
    engine = _build_db()
    with Session(engine) as db:
        now = datetime.now(tz=UTC).replace(tzinfo=None)
        pred = Prediction(
            fund_code="110022",
            horizon="short",
            up_probability=0.8,
            expected_return_pct=2.1,
            confidence=0.75,
            as_of=now,
        )
        db.add(pred)
        db.commit()
        db.refresh(pred)

        upsert_alert_rule(
            db,
            user_id="u1",
            fund_code="110022",
            horizon="short",
            min_up_probability=0.6,
            min_confidence=0.55,
            min_expected_return_pct=0.0,
            enabled=True,
        )
        events = evaluate_and_record_alert_events(
            db,
            fund_code="110022",
            horizon="short",
            prediction_id=pred.id,
        )
        assert len(events) == 1
        db.commit()

        hits = check_user_alerts(db, user_id="u1")
        assert len(hits) == 1
        assert hits[0]["fund_code"] == "110022"


def test_ab_summary_flow():
    engine = _build_db()
    with Session(engine) as db:
        now = datetime.now(tz=UTC).replace(tzinfo=None)
        upsert_ab_result(
            db,
            fund_code="110022",
            horizon="short",
            as_of=now,
            baseline_up_probability=0.55,
            baseline_expected_return_pct=0.8,
            candidate_up_probability=0.58,
            candidate_expected_return_pct=1.0,
            actual_return_pct=0.9,
        )
        upsert_ab_result(
            db,
            fund_code="161725",
            horizon="short",
            as_of=now,
            baseline_up_probability=0.52,
            baseline_expected_return_pct=0.6,
            candidate_up_probability=0.49,
            candidate_expected_return_pct=0.3,
            actual_return_pct=-0.4,
        )
        db.commit()

        rows = list_latest_ab_results(db, horizon="short", limit=10)
        assert len(rows) == 2
        summary = ab_summary(db, horizon="short")
        assert summary["sample_size"] == 2
        assert 0.0 <= summary["candidate_win_rate"] <= 1.0
