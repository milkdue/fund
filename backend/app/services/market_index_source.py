from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from statistics import pstdev

import httpx

from app.core.config import settings
from app.services.source_rate_limiter import RateLimitExceededError, rate_limiter

INDEX_DEFS = {
    "HS300": {"secid": "1.000300", "name": "沪深300"},
    "CSI500": {"secid": "0.399905", "name": "中证500"},
    "CHINEXT": {"secid": "0.399006", "name": "创业板指"},
}

KLINE_URL = (
    "https://push2his.eastmoney.com/api/qt/stock/kline/get?"
    "secid={secid}&klt=101&fqt=1&lmt={limit}&end=20500000&iscca=1&"
    "fields1=f1,f2,f3,f4,f5,f6&fields2=f51,f52,f53,f54,f55,f56,f57,f58"
)


@dataclass
class MarketIndexSnapshot:
    index_code: str
    index_name: str
    as_of: datetime
    close: float
    daily_change_pct: float
    volatility_20d: float
    momentum_5d: float


class MarketIndexError(Exception):
    pass


class MarketIndexRateLimitError(MarketIndexError):
    pass


def _calc_volatility_20d(closes: list[float]) -> float:
    window = closes[-21:]
    if len(window) < 3:
        return 0.0
    returns = []
    for i in range(1, len(window)):
        prev = window[i - 1]
        curr = window[i]
        if prev == 0:
            continue
        returns.append((curr - prev) / prev * 100)
    if len(returns) < 2:
        return 0.0
    return round(pstdev(returns), 2)


def _calc_daily_change(closes: list[float]) -> float:
    if len(closes) < 2 or closes[-2] == 0:
        return 0.0
    return round((closes[-1] - closes[-2]) / closes[-2] * 100, 2)


def _calc_momentum_5d(closes: list[float]) -> float:
    if len(closes) < 6 or closes[-6] == 0:
        return 0.0
    return round((closes[-1] - closes[-6]) / closes[-6] * 100, 2)


def fetch_index_snapshot(index_code: str, limit: int = 40, timeout_seconds: float = 8.0) -> MarketIndexSnapshot:
    info = INDEX_DEFS.get(index_code.upper())
    if not info:
        raise MarketIndexError(f"unsupported index code: {index_code}")

    try:
        rate_limiter.acquire_or_raise("eastmoney_market", settings.source_market_limit_per_min)
    except RateLimitExceededError as exc:
        raise MarketIndexRateLimitError(str(exc)) from exc

    url = KLINE_URL.format(secid=info["secid"], limit=max(25, min(limit, 120)))
    headers = {"User-Agent": "Mozilla/5.0 (FundPredictorMVP/1.0)"}
    try:
        response = httpx.get(url, timeout=timeout_seconds, headers=headers)
    except Exception as exc:
        raise MarketIndexError(f"request failed: {exc}") from exc

    if response.status_code != 200:
        raise MarketIndexError(f"source http status {response.status_code}")

    payload = response.json()
    data = payload.get("data") if isinstance(payload, dict) else None
    klines = data.get("klines") if isinstance(data, dict) else None
    if not isinstance(klines, list) or not klines:
        raise MarketIndexError("empty kline payload")

    closes: list[float] = []
    as_of: datetime | None = None
    for row in klines:
        # Format: 2026-03-10,3670.23,3681.45,3690.11,3658.66,123456,7890,0.45,...
        parts = str(row).split(",")
        if len(parts) < 3:
            continue
        try:
            date_str = parts[0]
            close = float(parts[2])
            as_of = datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            continue
        closes.append(close)

    if len(closes) < 2 or as_of is None:
        raise MarketIndexError("insufficient index data")

    return MarketIndexSnapshot(
        index_code=index_code.upper(),
        index_name=info["name"],
        as_of=as_of,
        close=round(closes[-1], 2),
        daily_change_pct=_calc_daily_change(closes),
        volatility_20d=_calc_volatility_20d(closes),
        momentum_5d=_calc_momentum_5d(closes),
    )
