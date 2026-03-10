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

    pred = client.get(f"/v1/funds/{code}/predict", params={"horizon": "short"})
    assert pred.status_code == 200
    assert 0 <= pred.json()["up_probability"] <= 1
    assert "model_version" in pred.json()

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

    walkforward = client.get("/v1/model/backtest/walkforward", params={"horizon": "short"})
    assert walkforward.status_code == 200
    assert "window_count" in walkforward.json()
