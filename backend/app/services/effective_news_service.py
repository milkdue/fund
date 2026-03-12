from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import NewsRaw
from app.services.news_sentiment import _clamp
from app.services.time_utils import shanghai_now_naive


@dataclass
class EffectiveNewsSignal:
    trade_date: str
    headline_count: int
    sentiment_score: float
    event_score: float
    volume_shock: float
    sample_title: str
    latest_published_at: datetime | None
    latest_age_days: float | None
    impact_strength: str
    impact_summary: str


def _sentiment_decay(days: float) -> float:
    if days <= 2:
        return 1.0
    if days <= 5:
        return 0.7
    if days <= 10:
        return 0.4
    return 0.15


def _event_decay(days: float) -> float:
    if days <= 2:
        return 1.0
    if days <= 5:
        return 0.85
    if days <= 10:
        return 0.6
    if days <= 21:
        return 0.35
    return 0.15


def _volume_decay(days: float) -> float:
    if days <= 1:
        return 1.0
    if days <= 3:
        return 0.8
    if days <= 7:
        return 0.45
    return 0.15


def _impact_strength(composite: float, latest_age_days: float | None, headline_count: int) -> str:
    if headline_count <= 0 or latest_age_days is None:
        return "neutral"
    if latest_age_days > 10:
        return "weak"
    if abs(composite) >= 0.4 or latest_age_days <= 2:
        return "strong"
    if abs(composite) >= 0.18 or latest_age_days <= 5:
        return "medium"
    return "weak"


def _impact_summary(*, strength: str, latest_age_days: float | None, headline_count: int, sample_title: str) -> str:
    if headline_count <= 0:
        return "当前没有抓到足够的公告或外部新闻样本，新闻影响按中性处理。"
    age_text = "暂无最近事件时间"
    if latest_age_days is not None:
        if latest_age_days < 1:
            age_text = "最近事件发生在 1 天内"
        else:
            age_text = f"最近事件距今约 {latest_age_days:.1f} 天"
    strength_text = {
        "strong": "短期影响较强",
        "medium": "短期影响中等",
        "weak": "短期影响较弱",
        "neutral": "当前影响中性",
    }.get(strength, "当前影响中性")
    return f"{age_text}，{strength_text}。代表性事件：{sample_title}"


def build_effective_news_signal(
    db: Session,
    code: str,
    *,
    reference_time: datetime | None = None,
    lookback_days: int = 21,
) -> EffectiveNewsSignal:
    ref = reference_time or shanghai_now_naive()
    cutoff = ref - timedelta(days=lookback_days)
    rows = list(
        db.scalars(
            select(NewsRaw)
            .where(NewsRaw.fund_code == code, NewsRaw.published_at >= cutoff)
            .order_by(NewsRaw.published_at.desc())
            .limit(120)
        )
    )
    if not rows:
        return EffectiveNewsSignal(
            trade_date=ref.date().isoformat(),
            headline_count=0,
            sentiment_score=0.0,
            event_score=0.0,
            volume_shock=0.0,
            sample_title="暂无新增公告/舆情",
            latest_published_at=None,
            latest_age_days=None,
            impact_strength="neutral",
            impact_summary="当前没有抓到足够的公告或外部新闻样本，新闻影响按中性处理。",
        )

    latest = rows[0]
    latest_age_days = max(0.0, round((ref - latest.published_at).total_seconds() / 86400, 1))

    sentiment_weight_sum = 0.0
    sentiment_total = 0.0
    event_weight_sum = 0.0
    event_total = 0.0
    recent_attention = 0.0
    old_attention = 0.0

    for row in rows:
        age_days = max(0.0, (ref - row.published_at).total_seconds() / 86400)
        s_weight = _sentiment_decay(age_days)
        e_weight = _event_decay(age_days)
        v_weight = _volume_decay(age_days)
        sentiment_total += row.sentiment_score * s_weight
        event_total += row.event_score * e_weight
        sentiment_weight_sum += s_weight
        event_weight_sum += e_weight
        if age_days <= 3:
            recent_attention += v_weight
        else:
            old_attention += v_weight

    sentiment_score = round(sentiment_total / sentiment_weight_sum, 4) if sentiment_weight_sum else 0.0
    event_score = round(event_total / event_weight_sum, 4) if event_weight_sum else 0.0
    baseline = max(old_attention / 3.0, 0.8)
    volume_shock = round(_clamp((recent_attention - baseline) / baseline, -1.0, 2.0), 4)
    composite = 0.5 * sentiment_score + 0.4 * event_score + 0.1 * volume_shock
    strength = _impact_strength(composite, latest_age_days, len(rows))
    sample_title = latest.title or "暂无新增公告/舆情"

    return EffectiveNewsSignal(
        trade_date=latest.published_at.date().isoformat(),
        headline_count=len(rows),
        sentiment_score=sentiment_score,
        event_score=event_score,
        volume_shock=volume_shock,
        sample_title=sample_title[:256],
        latest_published_at=latest.published_at,
        latest_age_days=latest_age_days,
        impact_strength=strength,
        impact_summary=_impact_summary(
            strength=strength,
            latest_age_days=latest_age_days,
            headline_count=len(rows),
            sample_title=sample_title[:80],
        ),
    )
