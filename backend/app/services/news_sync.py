from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Fund, NewsRaw, NewsSignalDaily
from app.services.news_feed_service import NewsFeedError, NewsFeedRateLimitError, fetch_fund_news_feed
from app.services.news_sentiment import aggregate_scores, score_headline, volume_shock


@dataclass
class NewsSyncResult:
    code: str
    fetched_count: int
    inserted_count: int
    trade_date: date


class NewsSyncError(Exception):
    pass


class NewsSyncRateLimitError(NewsSyncError):
    pass


def _hash_title(title: str) -> str:
    normalized = " ".join(title.strip().split())
    return hashlib.sha1(normalized.encode("utf-8")).hexdigest()


def _upsert_signal(
    db: Session,
    code: str,
    trade_date: date,
    headline_count: int,
    sentiment: float,
    event: float,
    shock: float,
    sample_title: str,
) -> NewsSignalDaily:
    row = db.scalar(
        select(NewsSignalDaily).where(
            NewsSignalDaily.fund_code == code,
            NewsSignalDaily.trade_date == trade_date,
        )
    )
    if not row:
        row = NewsSignalDaily(
            fund_code=code,
            trade_date=trade_date,
            headline_count=headline_count,
            sentiment_score=sentiment,
            event_score=event,
            volume_shock=shock,
            sample_title=sample_title[:256],
            updated_at=datetime.now(tz=UTC).replace(tzinfo=None),
        )
        db.add(row)
    else:
        row.headline_count = headline_count
        row.sentiment_score = sentiment
        row.event_score = event
        row.volume_shock = shock
        row.sample_title = sample_title[:256]
        row.updated_at = datetime.now(tz=UTC).replace(tzinfo=None)
    return row


def _rebuild_daily_signal(db: Session, code: str, trade_date: date) -> NewsSignalDaily:
    day_start = datetime.combine(trade_date, time.min)
    day_end = day_start + timedelta(days=1)
    rows = list(
        db.scalars(
            select(NewsRaw)
            .where(
                NewsRaw.fund_code == code,
                NewsRaw.published_at >= day_start,
                NewsRaw.published_at < day_end,
            )
            .order_by(NewsRaw.published_at.desc())
            .limit(500)
        )
    )

    if not rows:
        fallback_start = day_start - timedelta(days=3)
        rows = list(
            db.scalars(
                select(NewsRaw)
                .where(
                    NewsRaw.fund_code == code,
                    NewsRaw.published_at >= fallback_start,
                    NewsRaw.published_at < day_end,
                )
                .order_by(NewsRaw.published_at.desc())
                .limit(120)
            )
        )

    headline_count = len(rows)
    sentiment, event = aggregate_scores((r.sentiment_score, r.event_score) for r in rows)
    sample_title = rows[0].title if rows else "暂无新增公告/舆情"

    history_rows = list(
        db.scalars(
            select(NewsSignalDaily)
            .where(
                NewsSignalDaily.fund_code == code,
                NewsSignalDaily.trade_date < trade_date,
            )
            .order_by(NewsSignalDaily.trade_date.desc())
            .limit(7)
        )
    )
    history_counts = [r.headline_count for r in history_rows if r.headline_count > 0]
    shock = volume_shock(headline_count, history_counts)

    return _upsert_signal(
        db=db,
        code=code,
        trade_date=trade_date,
        headline_count=headline_count,
        sentiment=sentiment,
        event=event,
        shock=shock,
        sample_title=sample_title,
    )


def refresh_news_signals_for_code(db: Session, code: str, max_headlines: int = 20, trade_date: date | None = None) -> NewsSyncResult:
    target_date = trade_date or datetime.now(tz=UTC).date()
    fetched_count = 0
    inserted_count = 0
    fund = db.scalar(select(Fund).where(Fund.code == code))
    fund_name = fund.name if fund else None

    try:
        headlines = fetch_fund_news_feed(code=code, name=fund_name, limit=max_headlines)
    except NewsFeedRateLimitError as exc:
        raise NewsSyncRateLimitError(str(exc)) from exc
    except NewsFeedError as exc:
        raise NewsSyncError(str(exc)) from exc

    fetched_count = len(headlines)
    for item in headlines:
        title_hash = _hash_title(item.title)
        existing = db.scalar(
            select(NewsRaw.id).where(
                NewsRaw.fund_code == code,
                NewsRaw.title_hash == title_hash,
                NewsRaw.published_at == item.published_at,
            )
        )
        if existing:
            continue
        sentiment, event = score_headline(item.title)
        db.add(
            NewsRaw(
                fund_code=code,
                source=item.source,
                title=item.title,
                title_hash=title_hash,
                url=item.url,
                published_at=item.published_at,
                sentiment_score=sentiment,
                event_score=event,
                created_at=datetime.now(tz=UTC).replace(tzinfo=None),
            )
        )
        inserted_count += 1

    _rebuild_daily_signal(db, code=code, trade_date=target_date)
    db.commit()

    return NewsSyncResult(
        code=code,
        fetched_count=fetched_count,
        inserted_count=inserted_count,
        trade_date=target_date,
    )
