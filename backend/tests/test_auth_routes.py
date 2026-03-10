from contextlib import contextmanager

from app.core.config import settings


@contextmanager
def _auth_config(
    *,
    enabled: bool,
    bearer: str | None = None,
    token_map: str | None = None,
    default_user_id: str = "authorized-user",
):
    old_enabled = settings.auth_enabled
    old_bearer = settings.auth_bearer_token
    old_map = settings.auth_token_map
    old_default = settings.auth_default_user_id
    settings.auth_enabled = enabled
    settings.auth_bearer_token = bearer
    settings.auth_token_map = token_map
    settings.auth_default_user_id = default_user_id
    try:
        yield
    finally:
        settings.auth_enabled = old_enabled
        settings.auth_bearer_token = old_bearer
        settings.auth_token_map = old_map
        settings.auth_default_user_id = old_default


def test_public_routes_still_open_when_auth_enabled(client):
    with _auth_config(enabled=True, bearer="token-public"):
        res = client.get("/v1/funds/hot")
        assert res.status_code == 200


def test_user_route_requires_auth_when_enabled(client):
    with _auth_config(enabled=True, bearer="token-need-auth"):
        res = client.get("/v1/user/watchlist")
        assert res.status_code == 401
        res2 = client.get("/v1/user/watchlist/insights")
        assert res2.status_code == 401
        res_events = client.get("/v1/user/alerts/events")
        assert res_events.status_code == 401
        res_push_test = client.post("/v1/user/alerts/push-test", json={})
        assert res_push_test.status_code == 401
        res3 = client.post("/v1/user/events", json={"event_name": "app_open"})
        assert res3.status_code == 401


def test_user_route_accepts_valid_single_bearer(client):
    with _auth_config(enabled=True, bearer="token-one"):
        add = client.post(
            "/v1/user/watchlist",
            headers={
                "Authorization": "Bearer token-one",
                "X-User-Id": "tester-a",
            },
            json={"fund_code": "110022"},
        )
        assert add.status_code == 200
        assert add.json()["user_id"] == "tester-a"

        insights = client.get(
            "/v1/user/watchlist/insights",
            headers={"Authorization": "Bearer token-one", "X-User-Id": "tester-a"},
        )
        assert insights.status_code == 200

        events = client.get(
            "/v1/user/alerts/events",
            headers={"Authorization": "Bearer token-one", "X-User-Id": "tester-a"},
        )
        assert events.status_code == 200

        push_test = client.post(
            "/v1/user/alerts/push-test",
            headers={"Authorization": "Bearer token-one", "X-User-Id": "tester-a"},
            json={},
        )
        assert push_test.status_code == 200

        event = client.post(
            "/v1/user/events",
            headers={"Authorization": "Bearer token-one", "X-User-Id": "tester-a"},
            json={"event_name": "app_open"},
        )
        assert event.status_code == 200


def test_user_route_accepts_token_map_and_sets_mapped_user(client):
    with _auth_config(enabled=True, token_map="tok-a:user-a,tok-b:user-b"):
        add = client.post(
            "/v1/user/watchlist",
            headers={"Authorization": "Bearer tok-b"},
            json={"fund_code": "161725"},
        )
        assert add.status_code == 200
        assert add.json()["user_id"] == "user-b"

        bad = client.post(
            "/v1/user/watchlist",
            headers={"Authorization": "Bearer tok-c"},
            json={"fund_code": "161725"},
        )
        assert bad.status_code == 401
