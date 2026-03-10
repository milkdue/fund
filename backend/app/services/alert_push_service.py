from __future__ import annotations

from urllib.parse import quote

import httpx

from app.core.config import settings
from app.models.entities import AlertEvent
from app.services.source_rate_limiter import RateLimitExceededError, rate_limiter


def _is_enabled() -> bool:
    return bool(settings.bark_enabled and (settings.bark_user_key or "").strip())


def _bark_url(title: str, body: str) -> str:
    base = settings.bark_base_url.rstrip("/")
    key = quote((settings.bark_user_key or "").strip(), safe="")
    title_seg = quote(title.strip()[:120] or "基金阈值提醒", safe="")
    body_seg = quote(body.strip()[:512] or "预测信号触发提醒", safe="")
    return f"{base}/{key}/{title_seg}/{body_seg}"


def push_bark_message(*, title: str, body: str) -> bool:
    if not _is_enabled():
        return False

    try:
        rate_limiter.acquire_or_raise("bark_push", settings.bark_limit_per_min)
    except RateLimitExceededError:
        return False

    url = _bark_url(title=title, body=body)
    params: dict[str, str] = {}
    if (settings.bark_icon_url or "").strip():
        params["icon"] = settings.bark_icon_url.strip()
    if (settings.bark_group or "").strip():
        params["group"] = settings.bark_group.strip()

    timeout_s = max(2.0, settings.bark_timeout_ms / 1000.0)
    try:
        resp = httpx.get(url, params=params, timeout=timeout_s)
    except Exception:
        return False
    return resp.status_code == 200


def push_alert_event_to_bark(event: AlertEvent) -> bool:
    title = f"基金阈值提醒 {event.fund_code}"
    body = f"{event.horizon} | {event.message}"
    return push_bark_message(title=title, body=body)
