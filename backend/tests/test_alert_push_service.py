from app.core.config import settings
from app.services.alert_push_service import push_bark_message


class _DummyResp:
    def __init__(self, status_code: int):
        self.status_code = status_code


def test_push_bark_message_disabled():
    old_enabled = settings.bark_enabled
    old_key = settings.bark_user_key
    settings.bark_enabled = False
    settings.bark_user_key = None
    try:
        ok = push_bark_message(title="t", body="b")
    finally:
        settings.bark_enabled = old_enabled
        settings.bark_user_key = old_key
    assert ok is False


def test_push_bark_message_enabled(monkeypatch):
    captured = {}

    def _mock_get(url, params=None, timeout=None):
        captured["url"] = url
        captured["params"] = params or {}
        captured["timeout"] = timeout
        return _DummyResp(200)

    old_enabled = settings.bark_enabled
    old_base = settings.bark_base_url
    old_key = settings.bark_user_key
    old_icon = settings.bark_icon_url
    old_group = settings.bark_group
    old_timeout = settings.bark_timeout_ms
    old_limit = settings.bark_limit_per_min
    settings.bark_enabled = True
    settings.bark_base_url = "https://api.day.app"
    settings.bark_user_key = "dummy_user_key"
    settings.bark_icon_url = "https://example.com/icon.png"
    settings.bark_group = "fund_predictor"
    settings.bark_timeout_ms = 3000
    settings.bark_limit_per_min = 9999
    monkeypatch.setattr("app.services.alert_push_service.httpx.get", _mock_get)

    try:
        ok = push_bark_message(title="标题", body="内容")
    finally:
        settings.bark_enabled = old_enabled
        settings.bark_base_url = old_base
        settings.bark_user_key = old_key
        settings.bark_icon_url = old_icon
        settings.bark_group = old_group
        settings.bark_timeout_ms = old_timeout
        settings.bark_limit_per_min = old_limit

    assert ok is True
    assert "dummy_user_key" in captured["url"]
    assert captured["params"]["group"] == "fund_predictor"
