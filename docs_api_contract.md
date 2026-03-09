# API Contract v1 (for Android now, iOS later)

Base path: `/v1`

## Error envelope
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "resource not found",
    "timestamp": "2026-03-07T02:00:00Z"
  }
}
```

When upstream source rate limit is hit, API returns HTTP `429` with standard error envelope.

## Endpoints
- `GET /funds/search?q=` -> `[{code,name,category}]` (local DB first, then Eastmoney remote completion + cache)
- `GET /funds/hot` -> `[{code,name,category}]` (hot ranking, cache-backed)
- `GET /funds/{code}/quote` -> `{code,as_of,nav,daily_change_pct,volatility_20d}`
- `GET /funds/{code}/predict?horizon=short|mid` -> `{code,horizon,as_of,up_probability,expected_return_pct,confidence}`
- `GET /funds/{code}/explain?horizon=short|mid` -> `{code,horizon,confidence_interval_pct,top_factors[]}`
- `GET /user/watchlist` -> `[{user_id,fund_code}]`
- `POST /user/watchlist` with `{fund_code}` -> `{user_id,fund_code}`
- `GET /model/health` -> `{short_model_version,mid_model_version,last_train_at,coverage_rate}`
- `GET /system/data-sources` -> `{sources:[{name,purpose,url}]}`
- `GET /internal/cron/daily-refresh` -> daily batch refresh result (requires `Authorization: Bearer <CRON_SECRET>`)
