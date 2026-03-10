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
- `GET /funds/{code}/quote` -> `{code,as_of,data_freshness,nav,daily_change_pct,volatility_20d}`
- `GET /funds/{code}/predict?horizon=short|mid` -> `{code,horizon,as_of,data_freshness,up_probability,expected_return_pct,confidence}`
- `GET /funds/{code}/explain?horizon=short|mid` -> `{code,horizon,data_freshness,confidence_interval_pct,top_factors[],risk_flags[]}`（含行情+公告/舆情因子贡献）
- `GET /funds/{code}/kline` -> `{code,is_synthetic,note,items[]}`（由净值估算，非真实OHLC）
- `GET /funds/{code}/news-signal` -> `{code,trade_date,headline_count,sentiment_score,event_score,volume_shock,sample_title}`
- `POST /funds/{code}/feedback` with `{horizon,is_helpful,score,comment}` -> feedback item
- `GET /funds/{code}/feedback/summary?horizon=short|mid` -> feedback aggregation
- `GET /user/watchlist` -> `[{user_id,fund_code}]`
- `POST /user/watchlist` with `{fund_code}` -> `{user_id,fund_code}`
- `GET /user/alerts` -> alert rules
- `POST /user/alerts` -> upsert alert rule
- `GET /user/alerts/check` -> triggered alert items
- `GET /model/health` -> `{short_model_version,mid_model_version,last_train_at,coverage_rate}`
- `GET /model/backtest/latest?horizon=short|mid` -> `{horizon,generated_at,report_date,window_days,model_version,metrics}`
- `GET /model/ab/latest?horizon=short|mid&limit=20` -> A/B rows
- `GET /model/ab/summary?horizon=short|mid` -> A/B win-rate summary
- `GET /system/data-sources` -> `{sources:[{name,purpose,url}]}`
- `GET /system/market-context` -> `{market_score,style_score,data_freshness,source_degraded}`
- `GET /internal/cron/daily-refresh` -> daily batch refresh result (requires `Authorization: Bearer <CRON_SECRET>`)
- `GET /internal/cron/weekly-backtest` -> weekly backtest report generation (requires `Authorization: Bearer <CRON_SECRET>`)
