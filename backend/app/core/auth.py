from __future__ import annotations

from fastapi import Header, HTTPException

from app.core.config import settings


def _parse_token_map(raw: str | None) -> dict[str, str]:
    text = (raw or "").strip()
    if not text:
        return {}
    pairs: dict[str, str] = {}
    for part in text.split(","):
        item = part.strip()
        if not item:
            continue
        if ":" in item:
            token, user_id = item.split(":", 1)
            token = token.strip()
            user_id = user_id.strip()
            if token and user_id:
                pairs[token] = user_id
        else:
            token = item.strip()
            if token:
                pairs[token] = settings.auth_default_user_id
    return pairs


def get_current_user_id(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> str:
    # Backward-compatible default mode.
    if not settings.auth_enabled:
        return (x_user_id or "demo-user").strip() or "demo-user"

    if not authorization:
        raise HTTPException(status_code=401, detail="authorization header required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        raise HTTPException(status_code=401, detail="invalid authorization header")
    token = token.strip()

    token_map = _parse_token_map(settings.auth_token_map)
    if token_map:
        user_id = token_map.get(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="invalid bearer token")
        return user_id

    configured = (settings.auth_bearer_token or "").strip()
    if not configured:
        raise HTTPException(status_code=503, detail="auth is enabled but token is not configured")
    if token != configured:
        raise HTTPException(status_code=401, detail="invalid bearer token")

    return (x_user_id or settings.auth_default_user_id).strip() or settings.auth_default_user_id
