from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
import re

import httpx

from app.core.config import settings
from app.services.source_rate_limiter import RateLimitExceededError, rate_limiter

FUND_GZ_URL = "https://fundgz.1234567.com.cn/js/{code}.js?rt={version}"


@dataclass
class IntradayEstimateSnapshot:
    code: str
    name: str
    as_of: datetime
    estimate_nav: float
    estimate_change_pct: float
    source: str = "eastmoney_fundgz"


class IntradayEstimateError(Exception):
    pass


class IntradayEstimateRateLimitError(IntradayEstimateError):
    pass


def _extract_payload(raw: str) -> dict:
    text = raw.strip().lstrip("\ufeff")
    match = re.search(r"jsonpgz\((\{.*\})\)", text, re.S)
    if not match:
        raise IntradayEstimateError(f"unexpected estimate payload: {text[:80]}")
    try:
        return json.loads(match.group(1))
    except Exception as exc:
        raise IntradayEstimateError(f"invalid estimate payload: {exc}") from exc


def fetch_intraday_estimate(code: str, timeout_seconds: float = 8.0) -> IntradayEstimateSnapshot:
    try:
        rate_limiter.acquire_or_raise("eastmoney_estimate", settings.source_estimate_limit_per_min)
    except RateLimitExceededError as exc:
        raise IntradayEstimateRateLimitError(str(exc)) from exc

    version = int(datetime.now(tz=UTC).timestamp() * 1000)
    url = FUND_GZ_URL.format(code=code, version=version)
    headers = {"User-Agent": "Mozilla/5.0 (FundPredictorMVP/1.0)"}
    try:
        response = httpx.get(url, timeout=timeout_seconds, headers=headers)
    except Exception as exc:
        raise IntradayEstimateError(f"request failed: {exc}") from exc
    if response.status_code != 200:
        raise IntradayEstimateError(f"source http status {response.status_code}")

    payload = _extract_payload(response.text)
    estimate_nav = payload.get("gsz")
    estimate_change_pct = payload.get("gszzl")
    estimate_time = payload.get("gztime")
    if estimate_nav in {None, ""} or estimate_time in {None, ""}:
        raise IntradayEstimateError("estimate payload missing gsz or gztime")

    try:
        as_of = datetime.strptime(str(estimate_time), "%Y-%m-%d %H:%M")
    except ValueError as exc:
        raise IntradayEstimateError(f"invalid estimate time: {estimate_time}") from exc

    return IntradayEstimateSnapshot(
        code=str(payload.get("fundcode") or code),
        name=str(payload.get("name") or f"基金{code}"),
        as_of=as_of,
        estimate_nav=round(float(str(estimate_nav).strip()), 4),
        estimate_change_pct=round(float(str(estimate_change_pct).strip()), 2),
    )
