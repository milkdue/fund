from datetime import UTC, datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.session import Base
from app.models.entities import NewsRaw
from app.services.effective_news_service import build_effective_news_signal


def _dt(days_ago: float) -> datetime:
    return (datetime.now(tz=UTC) - timedelta(days=days_ago)).replace(tzinfo=None)


def test_recent_news_outweighs_old_news():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        db.add_all(
            [
                NewsRaw(
                    fund_code="110022",
                    source="tavily_news",
                    title="最新利好公告",
                    title_hash="a",
                    url=None,
                    published_at=_dt(0.5),
                    sentiment_score=0.8,
                    event_score=0.5,
                ),
                NewsRaw(
                    fund_code="110022",
                    source="eastmoney_announcement",
                    title="较早利空消息",
                    title_hash="b",
                    url=None,
                    published_at=_dt(12),
                    sentiment_score=-0.9,
                    event_score=-0.6,
                ),
            ]
        )
        db.commit()

        signal = build_effective_news_signal(db, "110022")
        assert signal.sentiment_score > 0
        assert signal.event_score > 0
        assert signal.impact_strength in {"strong", "medium"}
        assert signal.latest_age_days is not None and signal.latest_age_days < 2


def test_old_news_decays_to_weak_signal():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    with Session(engine) as db:
        db.add(
            NewsRaw(
                fund_code="161725",
                source="eastmoney_announcement",
                title="较久之前的事件",
                title_hash="c",
                url=None,
                published_at=_dt(14),
                sentiment_score=0.7,
                event_score=0.8,
            )
        )
        db.commit()

        signal = build_effective_news_signal(db, "161725")
        assert signal.latest_age_days is not None and signal.latest_age_days >= 10
        assert signal.impact_strength == "weak"
        assert "短期影响较弱" in signal.impact_summary
