from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import html
import re

import httpx

from app.core.config import settings
from app.services.source_rate_limiter import RateLimitExceededError, rate_limiter

ANNOUNCEMENT_URL = "https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjgg&code={code}&page=1&per={per}"


@dataclass
class NewsHeadline:
    title: str
    url: str | None
    source: str
    published_at: datetime


class NewsSourceError(Exception):
    pass


class NewsSourceRateLimitError(NewsSourceError):
    pass


def _strip_tags(value: str) -> str:
    return re.sub(r"<[^>]+>", "", value).replace("\xa0", " ").strip()


def _decode_content(payload: str) -> str:
    match = re.search(r'content:"(.*)"\s*,\s*records:', payload, re.S)
    if not match:
        return ""
    content_escaped = match.group(1)
    try:
        content = bytes(content_escaped, "utf-8").decode("unicode_escape")
    except Exception:
        content = content_escaped
    return html.unescape(content)


def _normalize_url(url: str) -> str:
    if url.startswith("//"):
        return f"https:{url}"
    if url.startswith("/"):
        return f"https://fundf10.eastmoney.com{url}"
    return url


def fetch_fund_announcements(code: str, limit: int = 20, timeout_seconds: float = 8.0) -> list[NewsHeadline]:
    if limit <= 0:
        return []

    try:
        rate_limiter.acquire_or_raise("eastmoney_news", settings.source_news_limit_per_min)
    except RateLimitExceededError as exc:
        raise NewsSourceRateLimitError(str(exc)) from exc

    url = ANNOUNCEMENT_URL.format(code=code, per=max(10, min(limit, 60)))
    headers = {"User-Agent": "Mozilla/5.0 (FundPredictorMVP/1.0)"}
    try:
        response = httpx.get(url, timeout=timeout_seconds, headers=headers)
    except Exception as exc:
        raise NewsSourceError(f"request failed: {exc}") from exc

    if response.status_code != 200:
        raise NewsSourceError(f"source http status {response.status_code}")

    payload = response.text.lstrip("\ufeff")
    content = _decode_content(payload)
    if not content:
        return []

    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", content, re.S)
    results: list[NewsHeadline] = []
    seen_titles: set[str] = set()

    for row in rows:
        link_match = re.search(r"<a[^>]*href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", row, re.S)
        if not link_match:
            continue

        title = _strip_tags(link_match.group(2))
        if not title or title in seen_titles:
            continue
        seen_titles.add(title)

        date_match = re.search(r"(\d{4}-\d{2}-\d{2})", row)
        if date_match:
            try:
                published_at = datetime.strptime(date_match.group(1), "%Y-%m-%d")
            except ValueError:
                published_at = datetime.now(tz=UTC).replace(tzinfo=None)
        else:
            published_at = datetime.now(tz=UTC).replace(tzinfo=None)

        results.append(
            NewsHeadline(
                title=title[:512],
                url=_normalize_url(link_match.group(1)),
                source="eastmoney_announcement",
                published_at=published_at,
            )
        )
        if len(results) >= limit:
            break

    return results
