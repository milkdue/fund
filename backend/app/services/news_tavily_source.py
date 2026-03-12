from __future__ import annotations

from datetime import UTC, datetime

import httpx

from app.core.config import settings
from app.services.news_source import NewsHeadline
from app.services.source_rate_limiter import RateLimitExceededError, rate_limiter

TAVILY_SEARCH_URL = "https://api.tavily.com/search"


class TavilyNewsError(Exception):
    pass


class TavilyNewsRateLimitError(TavilyNewsError):
    pass


def _parse_tavily_datetime(value: str | None) -> datetime:
    if not value:
        return datetime.now(tz=UTC).replace(tzinfo=None)
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text).astimezone(UTC).replace(tzinfo=None)
    except Exception:
        try:
            return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
        except Exception:
            return datetime.now(tz=UTC).replace(tzinfo=None)


def search_fund_news_with_tavily(*, code: str, name: str | None, limit: int = 6) -> list[NewsHeadline]:
    if not settings.tavily_enabled or not settings.tavily_api_key:
        return []

    try:
        rate_limiter.acquire_or_raise("tavily_news", settings.source_tavily_limit_per_min)
    except RateLimitExceededError as exc:
        raise TavilyNewsRateLimitError(str(exc)) from exc

    query_name = name or code
    payload = {
        "api_key": settings.tavily_api_key,
        "query": f"{query_name} {code} 基金 公告 舆情 新闻",
        "topic": "news",
        "search_depth": settings.tavily_search_depth,
        "days": settings.tavily_days,
        "max_results": max(1, min(limit, settings.tavily_max_results)),
    }
    try:
        response = httpx.post(TAVILY_SEARCH_URL, json=payload, timeout=settings.tavily_timeout_ms / 1000)
    except Exception as exc:
        raise TavilyNewsError(f"request failed: {exc}") from exc
    if response.status_code != 200:
        raise TavilyNewsError(f"source http status {response.status_code}: {response.text[:160]}")

    data = response.json()
    results = data.get("results") or []
    headlines: list[NewsHeadline] = []
    seen_titles: set[str] = set()
    for item in results:
        title = str(item.get("title") or "").strip()
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)
        headlines.append(
            NewsHeadline(
                title=title[:512],
                url=item.get("url"),
                source="tavily_news",
                published_at=_parse_tavily_datetime(
                    item.get("published_date") or item.get("published_at") or item.get("date")
                ),
            )
        )
    return headlines
