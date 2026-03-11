import json
import re
from dataclasses import dataclass

import httpx

from app.core.config import settings
from app.services.source_rate_limiter import RateLimitExceededError, rate_limiter

FUNDCODE_SEARCH_URL = "https://fund.eastmoney.com/js/fundcode_search.js"
UNSUPPORTED_NAME_MARKERS = ("(后端)", "（后端）")


@dataclass
class FundSearchResult:
    code: str
    name: str
    category: str


class FundSearchError(Exception):
    pass


class FundSearchRateLimitError(FundSearchError):
    pass


def _extract_list(script: str) -> list[list[str]]:
    # Expected format: var r = [["000001","xx","name","category"], ...];
    match = re.search(r"var\s+r\s*=\s*(\[.*\]);?", script, re.S)
    if not match:
        raise FundSearchError("search payload parse failed")
    raw = match.group(1)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FundSearchError(f"search payload json decode failed: {exc}") from exc


def _is_supported_result(name: str) -> bool:
    normalized = name.strip()
    return normalized != "" and not any(marker in normalized for marker in UNSUPPORTED_NAME_MARKERS)


def remote_search_funds(query: str, timeout_seconds: float = 8.0, limit: int = 20) -> list[FundSearchResult]:
    q = query.strip()
    if not q:
        return []

    try:
        rate_limiter.acquire_or_raise("eastmoney_search", settings.source_search_limit_per_min)
    except RateLimitExceededError as exc:
        raise FundSearchRateLimitError(str(exc)) from exc

    response = None
    last_error: Exception | None = None
    headers = {"User-Agent": "Mozilla/5.0 (FundPredictorMVP/1.0)"}
    for _ in range(2):
        try:
            response = httpx.get(FUNDCODE_SEARCH_URL, timeout=timeout_seconds, headers=headers)
            break
        except Exception as exc:
            last_error = exc
    if response is None:
        raise FundSearchError(f"request failed: {last_error}")

    if response.status_code != 200:
        raise FundSearchError(f"source http status {response.status_code}")

    rows = _extract_list(response.text)
    lowered = q.lower()

    results: list[FundSearchResult] = []
    for row in rows:
        if len(row) < 4:
            continue
        code, _, name, category = row[0], row[1], row[2], row[3]
        if not _is_supported_result(name):
            continue
        if lowered in code.lower() or lowered in name.lower():
            results.append(FundSearchResult(code=code, name=name, category=category or "未分类"))
        if len(results) >= limit:
            break

    return results
