from __future__ import annotations

from app.services.news_source import NewsHeadline, NewsSourceError, NewsSourceRateLimitError, fetch_fund_announcements
from app.services.news_tavily_source import TavilyNewsError, TavilyNewsRateLimitError, search_fund_news_with_tavily


class NewsFeedError(Exception):
    pass


class NewsFeedRateLimitError(NewsFeedError):
    pass


def _dedupe(items: list[NewsHeadline]) -> list[NewsHeadline]:
    seen: set[tuple[str, str | None]] = set()
    merged: list[NewsHeadline] = []
    for item in sorted(items, key=lambda row: row.published_at, reverse=True):
        key = (" ".join(item.title.split()), item.url)
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)
    return merged


def fetch_fund_news_feed(*, code: str, name: str | None, limit: int = 20) -> list[NewsHeadline]:
    items: list[NewsHeadline] = []
    errors: list[Exception] = []

    try:
        items.extend(fetch_fund_announcements(code, limit=min(limit, 20)))
    except NewsSourceRateLimitError as exc:
        errors.append(exc)
    except NewsSourceError as exc:
        errors.append(exc)

    try:
        items.extend(search_fund_news_with_tavily(code=code, name=name, limit=min(limit, 8)))
    except TavilyNewsRateLimitError as exc:
        errors.append(exc)
    except TavilyNewsError as exc:
        errors.append(exc)

    merged = _dedupe(items)
    if merged:
        return merged[:limit]

    if errors and all(isinstance(exc, (NewsSourceRateLimitError, TavilyNewsRateLimitError)) for exc in errors):
        raise NewsFeedRateLimitError(str(errors[0]))
    if errors:
        raise NewsFeedError(str(errors[0]))
    return []
