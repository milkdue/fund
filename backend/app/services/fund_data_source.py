import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from statistics import pstdev

import httpx

from app.core.config import settings
from app.services.source_rate_limiter import RateLimitExceededError, rate_limiter

PINGZHONGDATA_URL = "https://fund.eastmoney.com/pingzhongdata/{code}.js?v={version}"


@dataclass
class FundMarketSnapshot:
    code: str
    name: str
    as_of: datetime
    nav: float
    daily_change_pct: float
    volatility_20d: float


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
        # Fallback for JSON-like payloads: "fS_name":"xxx"
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


def fetch_latest_snapshot(code: str, timeout_seconds: float = 8.0) -> FundMarketSnapshot:
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
    as_of = datetime.fromtimestamp(ts_millis / 1000, tz=UTC).replace(tzinfo=None)

    return FundMarketSnapshot(
        code=code,
        name=fund_name,
        as_of=as_of,
        nav=round(net_values[-1], 4),
        daily_change_pct=_calc_daily_change(net_values),
        volatility_20d=_calc_volatility_20d(net_values),
    )
