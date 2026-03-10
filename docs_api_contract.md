# API Contract v1 (for Android now, iOS later)

Base path: `/v1`

## Authentication (optional)
- Default (`FUND_AUTH_ENABLED=false`): no bearer auth required.
- When `FUND_AUTH_ENABLED=true`, these endpoints require `Authorization: Bearer <token>`:
  - `POST /funds/{code}/feedback`
  - `GET /user/watchlist`
  - `POST /user/watchlist`
  - `GET /user/watchlist/insights`
  - `GET /user/alerts`
  - `POST /user/alerts`
  - `GET /user/alerts/check`
  - `POST /user/events`
  - `GET /user/weekly-report`
- Public行情与模型查询接口保持匿名可访问（如 `search/quote/predict/explain/kline/news-signal/model/*/system/*`）。
- Token 配置方式：
  - 单 token：`FUND_AUTH_BEARER_TOKEN=<token>`
  - 多 token 映射：`FUND_AUTH_TOKEN_MAP=token1:user1,token2:user2`（配置后优先）

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
- `GET /funds/{code}/predict?horizon=short|mid` -> `{code,horizon,as_of,data_freshness,up_probability,expected_return_pct,confidence,model_version,data_source,snapshot_id}`
- `GET /funds/{code}/prediction-change?horizon=short|mid` -> `{code,horizon,current_as_of,previous_as_of,data_freshness,up_probability_delta,expected_return_pct_delta,confidence_delta,changed_factors[],summary}`
- `GET /funds/{code}/explain?horizon=short|mid` -> `{code,horizon,data_freshness,confidence_interval_pct,top_factors[],risk_flags[]}`（含行情+公告/舆情因子贡献）
- `GET /funds/{code}/ai-judgement?horizon=short|mid` -> `{code,horizon,as_of,data_freshness,trend,trend_strength,agreement_with_model,key_reasons[],risk_warnings[],confidence_adjustment,adjusted_up_probability,summary,provider,model}`
- `GET /funds/{code}/kline` -> `{code,is_synthetic,note,items[]}`（由净值估算，非真实OHLC）
- `GET /funds/{code}/news-signal` -> `{code,trade_date,headline_count,sentiment_score,event_score,volume_shock,sample_title}`
- `POST /funds/{code}/feedback` with `{horizon,is_helpful,score,comment}` -> feedback item
- `GET /funds/{code}/feedback/summary?horizon=short|mid` -> feedback aggregation
- `GET /user/watchlist` -> `[{user_id,fund_code}]`
- `POST /user/watchlist` with `{fund_code}` -> `{user_id,fund_code}`
- `GET /user/watchlist/insights` -> `{user_id,generated_at,items:[{fund_code,short_up_probability,short_confidence,mid_up_probability,mid_confidence,data_freshness,risk_level,signal}]}`
- `GET /user/alerts` -> alert rules
- `POST /user/alerts` -> upsert alert rule
- `GET /user/alerts/check` -> triggered alert items
- `POST /user/events` with `{event_name,fund_code?,metadata?}` -> `{id,count,event_day}`
- `GET /user/weekly-report` -> `{user_id,from_date,to_date,audit_requests,event_counts,feedback_total,feedback_helpful_rate,alert_hits}`
- `GET /model/health` -> `{short_model_version,mid_model_version,last_train_at,coverage_rate}`
- `GET /model/backtest/latest?horizon=short|mid` -> `{horizon,generated_at,report_date,window_days,model_version,metrics}`
- `GET /model/backtest/walkforward?horizon=short|mid` -> `{horizon,generated_at,window_days,step_days,window_count,avg_accuracy,avg_auc,avg_f1,avg_annualized_return,worst_max_drawdown,avg_sharpe,windows[]}`
- `GET /model/ab/latest?horizon=short|mid&limit=20` -> A/B rows
- `GET /model/ab/summary?horizon=short|mid` -> A/B win-rate summary
- `GET /system/data-sources` -> `{sources:[{name,purpose,url}]}`
- `GET /system/data-health` -> `{generated_at,fund_pool_size,quote_coverage_48h,prediction_coverage_48h,latest_quote_at,latest_prediction_at,latest_news_trade_date,latest_market_at,quote_freshness,prediction_freshness,market_freshness,source_status}`
- `GET /system/market-context` -> `{market_score,style_score,data_freshness,source_degraded}`
- `GET /internal/cron/daily-refresh` -> daily batch refresh result (requires `Authorization: Bearer <CRON_SECRET>`)
- `GET /internal/cron/weekly-backtest` -> weekly backtest report generation (requires `Authorization: Bearer <CRON_SECRET>`)
