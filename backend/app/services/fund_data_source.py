import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from statistics import pstdev

import httpx

from app.core.config import settings
from app.services.akshare_source import AkshareSourceError, AkshareUnavailableError, fetch_open_fund_nav_snapshot
from app.services.source_rate_limiter import RateLimitExceededError, rate_limiter
from app.services.time_utils import epoch_ms_to_shanghai_naive

PINGZHONGDATA_URL = "https://fund.eastmoney.com/pingzhongdata/{code}.js?v={version}"


@dataclass
class FundMarketSnapshot:
    code: str
    name: str
    as_of: datetime
    nav: float
    daily_change_pct: float
    volatility_20d: float
    source: str = "eastmoney_pingzhongdata"


@dataclass
class KlinePoint:
    ts: datetime
    open: float
    high: float
    low: float
    close: float


class FundDataError(Exception):
    pass


class FundDataRateLimitError(FundDataError):
    pass


def _extract_var(script: str, var_name: str) -> str:
    patterns = [
        re.compile(rf"(?:var|let|const)\s+{re.escape(var_name)}\s*=\s*(.*?);", re.S),
        re.compile(rf"{re.escape(var_name)}\s*=\s*(.*?);", re.S),
    ]
    for pattern in patterns:
        match = pattern.search(script)
        if match:
            return match.group(1).strip()
    raise FundDataError(f"variable {var_name} not found")


def _load_json_value(script: str, var_name: str):
    raw = _extract_var(script, var_name)
    return json.loads(raw)


def _load_string_value(script: str, var_name: str) -> str:
    try:
        raw = _extract_var(script, var_name)
        return raw.strip().strip('"').strip("'")
    except FundDataError:
        match = re.search(rf'"{re.escape(var_name)}"\s*:\s*"([^"]+)"', script)
        if match:
            return match.group(1).strip()
        raise


def _calc_daily_change(net_values: list[float]) -> float:
    if len(net_values) < 2 or net_values[-2] == 0:
        return 0.0
    prev, last = net_values[-2], net_values[-1]
    return round((last - prev) / prev * 100, 2)


def _calc_volatility_20d(net_values: list[float]) -> float:
    window = net_values[-21:]
    if len(window) < 3:
        return 0.0

    returns: list[float] = []
    for idx in range(1, len(window)):
        prev = window[idx - 1]
        curr = window[idx]
        if prev == 0:
            continue
        returns.append((curr - prev) / prev * 100)

    if len(returns) < 2:
        return 0.0
    return round(pstdev(returns), 2)


def _fetch_source_script(code: str, timeout_seconds: float = 8.0) -> str:
    version = int(datetime.now(tz=UTC).timestamp() * 1000)
    url = PINGZHONGDATA_URL.format(code=code, version=version)
    try:
        rate_limiter.acquire_or_raise("eastmoney_nav", settings.source_nav_limit_per_min)
    except RateLimitExceededError as exc:
        raise FundDataRateLimitError(str(exc)) from exc

    response = None
    last_error: Exception | None = None
    headers = {"User-Agent": "Mozilla/5.0 (FundPredictorMVP/1.0)"}
    for _ in range(2):
        try:
            response = httpx.get(url, timeout=timeout_seconds, headers=headers)
            break
        except Exception as exc:
            last_error = exc
    if response is None:
        raise FundDataError(f"request failed: {last_error}")

    if response.status_code != 200:
        raise FundDataError(f"source http status {response.status_code}")

    script = response.text.lstrip("\ufeff").strip()
    if script.startswith("<"):
        raise FundDataError(f"unexpected html payload from source: {script[:80]}")
    return script


def fetch_latest_snapshot(code: str, timeout_seconds: float = 8.0) -> FundMarketSnapshot:
    errors: list[str] = []
    try:
        script = _fetch_source_script(code, timeout_seconds)
        fund_name = _load_string_value(script, "fS_name")
        trend = _load_json_value(script, "Data_netWorthTrend")

        if not trend:
            raise FundDataError("empty Data_netWorthTrend")

        sorted_points = sorted(trend, key=lambda item: item.get("x", 0))
        net_values = [float(point["y"]) for point in sorted_points if point.get("y") is not None]
        if not net_values:
            raise FundDataError("no valid net worth values")

        last_point = sorted_points[-1]
        ts_millis = int(last_point.get("x", 0))
        as_of = epoch_ms_to_shanghai_naive(ts_millis)

        return FundMarketSnapshot(
            code=code,
            name=fund_name,
            as_of=as_of,
            nav=round(net_values[-1], 4),
            daily_change_pct=_calc_daily_change(net_values),
            volatility_20d=_calc_volatility_20d(net_values),
            source="eastmoney_pingzhongdata",
        )
    except FundDataError as exc:
        errors.append(str(exc))

    if settings.akshare_enabled:
        try:
            ak_snapshot = fetch_open_fund_nav_snapshot(code)
            return FundMarketSnapshot(
                code=ak_snapshot.code,
                name=ak_snapshot.name,
                as_of=ak_snapshot.as_of,
                nav=ak_snapshot.nav,
                daily_change_pct=ak_snapshot.daily_change_pct,
                volatility_20d=ak_snapshot.volatility_20d,
                source=ak_snapshot.source,
            )
        except (AkshareUnavailableError, AkshareSourceError) as exc:
            errors.append(str(exc))

    raise FundDataError(" | ".join(errors) if errors else "snapshot unavailable")


def fetch_kline_points(code: str, days: int = 60, timeout_seconds: float = 8.0) -> list[KlinePoint]:
    script = _fetch_source_script(code, timeout_seconds)
    trend = _load_json_value(script, "Data_netWorthTrend")
    if not trend:
        raise FundDataError("empty Data_netWorthTrend")

    sorted_points = sorted(trend, key=lambda item: item.get("x", 0))
    values = [(int(p.get("x", 0)), float(p.get("y"))) for p in sorted_points if p.get("y") is not None]
    if len(values) < 2:
        raise FundDataError("insufficient net worth data")

    values = values[-max(10, min(days, 240)) :]
    candles: list[KlinePoint] = []
    prev_close = values[0][1]
    for ts_millis, close in values:
        open_price = prev_close
        diff_pct = abs((close - open_price) / open_price) if open_price else 0.0
        wick_pct = max(0.0015, min(0.03, diff_pct * 0.6 + 0.002))
        high = max(open_price, close) * (1.0 + wick_pct)
        low = min(open_price, close) * (1.0 - wick_pct)
        candles.append(
            KlinePoint(
                ts=epoch_ms_to_shanghai_naive(ts_millis),
                open=round(open_price, 4),
                high=round(high, 4),
                low=round(low, 4),
                close=round(close, 4),
            )
        )
        prev_close = close

    return candles
