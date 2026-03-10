from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import MarketIndexDaily
from app.services.market_index_source import INDEX_DEFS, MarketIndexError, MarketIndexRateLimitError, fetch_index_snapshot


@dataclass
class MarketContext:
    market_score: float
    style_score: float
    data_freshness: str
    source_degraded: bool


class MarketContextError(Exception):
    pass


class MarketContextRateLimitError(MarketContextError):
    pass


def _freshness(as_of: datetime | None) -> str:
    if as_of is None:
        return "stale"
    delta_hours = (datetime.utcnow() - as_of).total_seconds() / 3600
    if delta_hours <= 36:
        return "fresh"
    if delta_hours <= 72:
        return "lagging"
    return "stale"


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _score_from_rows(rows: dict[str, MarketIndexDaily]) -> tuple[float, float]:
    hs300 = rows.get("HS300")
    csi500 = rows.get("CSI500")
    chinext = rows.get("CHINEXT")
    if not hs300 or not csi500 or not chinext:
        return 0.0, 0.0

    market_daily = (hs300.daily_change_pct + csi500.daily_change_pct + chinext.daily_change_pct) / 3.0
    market_mom = (hs300.momentum_5d + csi500.momentum_5d + chinext.momentum_5d) / 3.0
    vol_penalty = (hs300.volatility_20d + csi500.volatility_20d + chinext.volatility_20d) / 3.0

    market_score = _clamp(market_daily * 0.35 + market_mom * 0.15 - vol_penalty * 0.08, -2.5, 2.5)
    style_score = _clamp(chinext.daily_change_pct - hs300.daily_change_pct, -3.0, 3.0)
    return round(market_score, 4), round(style_score, 4)


def refresh_market_indices(db: Session) -> dict[str, MarketIndexDaily]:
    rows: dict[str, MarketIndexDaily] = {}
    for code in INDEX_DEFS:
        try:
            snap = fetch_index_snapshot(code)
        except MarketIndexRateLimitError as exc:
            raise MarketContextRateLimitError(str(exc)) from exc
        except MarketIndexError as exc:
            raise MarketContextError(str(exc)) from exc

        row = db.scalar(
            select(MarketIndexDaily).where(
                MarketIndexDaily.index_code == snap.index_code,
                MarketIndexDaily.as_of == snap.as_of,
            )
        )
        if not row:
            row = MarketIndexDaily(
                index_code=snap.index_code,
                index_name=snap.index_name,
                as_of=snap.as_of,
                close=snap.close,
                daily_change_pct=snap.daily_change_pct,
                volatility_20d=snap.volatility_20d,
                momentum_5d=snap.momentum_5d,
            )
            db.add(row)
        else:
            row.close = snap.close
            row.daily_change_pct = snap.daily_change_pct
            row.volatility_20d = snap.volatility_20d
            row.momentum_5d = snap.momentum_5d
        rows[snap.index_code] = row

    db.commit()
    return rows


def latest_market_context(db: Session) -> MarketContext:
    latest_rows: dict[str, MarketIndexDaily] = {}
    newest_as_of: datetime | None = None
    for code in INDEX_DEFS:
        row = db.scalar(
            select(MarketIndexDaily)
            .where(MarketIndexDaily.index_code == code)
            .order_by(MarketIndexDaily.as_of.desc())
            .limit(1)
        )
        if row:
            latest_rows[code] = row
            if newest_as_of is None or row.as_of > newest_as_of:
                newest_as_of = row.as_of

    market_score, style_score = _score_from_rows(latest_rows)
    fresh = _freshness(newest_as_of)
    source_degraded = len(latest_rows) < len(INDEX_DEFS) or fresh == "stale"
    return MarketContext(
        market_score=market_score,
        style_score=style_score,
        data_freshness=fresh,
        source_degraded=source_degraded,
    )


def get_or_refresh_market_context(db: Session) -> MarketContext:
    ctx = latest_market_context(db)
    if ctx.data_freshness == "fresh" and not ctx.source_degraded:
        return ctx
    try:
        refresh_market_indices(db)
    except (MarketContextError, MarketContextRateLimitError):
        return ctx
    return latest_market_context(db)
