from datetime import datetime


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_end_to_end_read_flow(client):
    search = client.get("/v1/funds/search", params={"q": "易方达"})
    assert search.status_code == 200
    items = search.json()
    assert items

    code = items[0]["code"]
    quote = client.get(f"/v1/funds/{code}/quote")
    assert quote.status_code == 200
    assert quote.json()["quote_type"] == "official_nav"
    assert "quality_status" in quote.json()

    estimate = client.get(f"/v1/funds/{code}/estimate")
    assert estimate.status_code in {200, 502}

    pred = client.get(f"/v1/funds/{code}/predict", params={"horizon": "short"})
    assert pred.status_code == 200
    assert 0 <= pred.json()["up_probability"] <= 1
    assert "model_version" in pred.json()
    assert "scorecard" in pred.json()
    assert "total_score" in pred.json()["scorecard"]
    assert pred.json()["scorecard"]["components"][0]["detail_lines"]

    explain = client.get(f"/v1/funds/{code}/explain", params={"horizon": "short"})
    assert explain.status_code == 200
    assert explain.json()["top_factors"]

    change = client.get(f"/v1/funds/{code}/prediction-change", params={"horizon": "short"})
    assert change.status_code == 200
    assert "up_probability_delta" in change.json()

    ai = client.get(f"/v1/funds/{code}/ai-judgement", params={"horizon": "short"})
    assert ai.status_code == 200
    assert ai.json()["provider"]


def test_watchlist_flow(client):
    headers = {"X-User-Id": "android-user"}
    add = client.post("/v1/user/watchlist", headers=headers, json={"fund_code": "110022"})
    assert add.status_code == 200

    get_rows = client.get("/v1/user/watchlist", headers=headers)
    assert get_rows.status_code == 200
    assert get_rows.json()[0]["fund_code"] == "110022"

    insights = client.get("/v1/user/watchlist/insights", headers=headers)
    assert insights.status_code == 200
    assert insights.json()["items"][0]["action_label"]
    assert "score_summary" in insights.json()["items"][0]
    assert insights.json()["items"][0]["short_scorecard"]

    events = client.get("/v1/user/alerts/events", headers=headers)
    assert events.status_code == 200
    assert isinstance(events.json(), list)


def test_alert_push_test_endpoint(client, monkeypatch):
    from app.core.config import settings

    old_bark_enabled = settings.bark_enabled
    old_bark_key = settings.bark_user_key
    settings.bark_enabled = True
    settings.bark_user_key = "dummy-test-key"
    called: dict[str, str] = {}

    def _mock_push(*, title: str, body: str) -> bool:
        called["title"] = title
        called["body"] = body
        return True

    monkeypatch.setattr("app.api.v1.routes.push_bark_message", _mock_push)
    headers = {"X-User-Id": "android-user"}
    try:
        res = client.post(
            "/v1/user/alerts/push-test",
            headers=headers,
            json={
                "title": "提醒测试",
                "message": "这是测试推送",
                "fund_code": "110022",
                "horizon": "short",
                "emit_event": True,
            },
        )
        assert res.status_code == 200
        payload = res.json()
        assert payload["ok"] is True
        assert payload["sent"] is True
        assert payload["bark_enabled"] is True
        assert payload["event_id"] is not None
        assert called["title"] == "提醒测试"
        assert called["body"] == "这是测试推送"

        events = client.get("/v1/user/alerts/events", headers=headers)
        assert events.status_code == 200
        event_ids = {item["id"] for item in events.json()}
        assert payload["event_id"] in event_ids
    finally:
        settings.bark_enabled = old_bark_enabled
        settings.bark_user_key = old_bark_key


def test_estimate_endpoint_with_mocked_source(client, monkeypatch):
    from app.services.intraday_estimate_source import IntradayEstimateSnapshot

    monkeypatch.setattr(
        "app.api.v1.routes.fetch_intraday_estimate",
        lambda code: IntradayEstimateSnapshot(
            code=code,
            name=f"基金{code}",
            as_of=datetime(2026, 3, 12, 14, 30),
            estimate_nav=2.135,
            estimate_change_pct=1.26,
        ),
    )
    res = client.get("/v1/funds/110022/estimate")
    assert res.status_code == 200
    payload = res.json()
    assert payload["source"] == "eastmoney_fundgz"
    assert payload["source_label"]
    assert "quality_status" in payload


def test_hot_and_data_sources(client):
    hot = client.get("/v1/funds/hot")
    assert hot.status_code == 200
    assert isinstance(hot.json(), list)

    sources = client.get("/v1/system/data-sources")
    assert sources.status_code == 200
    payload = sources.json()
    assert "sources" in payload
    assert len(payload["sources"]) >= 2

    health = client.get("/v1/system/data-health")
    assert health.status_code == 200
    assert "fund_pool_size" in health.json()
    assert "latest_estimate_at" in health.json()

    walkforward = client.get("/v1/model/backtest/walkforward", params={"horizon": "short"})
    assert walkforward.status_code == 200
    assert "window_count" in walkforward.json()
