import os
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.fund import (
    AbCompareItem,
    AbSummaryResponse,
    AiJudgementResponse,
    AlertCheckResponse,
    AlertHitItem,
    AlertRuleIn,
    AlertRuleItem,
    BacktestMetrics,
    BacktestReportResponse,
    DataSourceItem,
    DataSourceResponse,
    ExplainResponse,
    FeedbackIn,
    FeedbackItem,
    FeedbackSummaryResponse,
    KlineItem,
    KlineResponse,
    FundItem,
    ModelHealthResponse,
    MarketContextResponse,
    NewsSignalResponse,
    PredictResponse,
    QuoteResponse,
    WatchlistIn,
    WatchlistItem,
)
from app.services.alerts_service import check_user_alerts, list_alert_rules, upsert_alert_rule
from app.services.backtest_service import generate_backtest_report
from app.services.feedback_service import add_feedback, feedback_summary
from app.services.market_context_service import get_or_refresh_market_context, latest_market_context
from app.services.model_health import get_model_health
from app.services.market_sync import MarketSyncError, MarketSyncRateLimitError, refresh_fund_data
from app.services.model_ab_service import ab_summary, list_latest_ab_results
from app.services.news_sync import NewsSyncError, NewsSyncRateLimitError, refresh_news_signals_for_code
from app.services.ai_second_opinion import AiSecondOpinionError, get_ai_second_opinion
from app.services.predictor import build_risk_flags, confidence_interval, explain_features
from app.services.fund_search_source import FundSearchError, FundSearchRateLimitError, remote_search_funds
from app.services.fund_data_source import FundDataError, fetch_kline_points
from app.services.fund_sync import upsert_funds
from app.services.hot_funds import hot_rank
from app.services.repository import (
    add_watchlist,
    get_watchlist,
    latest_backtest_report,
    latest_news_signal,
    latest_prediction,
    latest_quote,
    search_funds,
)
from app.workers.daily_job import run_daily_refresh
from app.workers.weekly_job import run_weekly_backtest

router = APIRouter(prefix="/v1")


def _verify_cron_auth(authorization: str | None) -> None:
    expected = os.getenv("CRON_SECRET") or settings.cron_secret
    if not expected:
        raise HTTPException(status_code=503, detail="cron secret is not configured")
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="invalid cron authorization")


def _refresh_news_signal_soft(db: Session, code: str) -> None:
    try:
        refresh_news_signals_for_code(db, code)
    except (NewsSyncError, NewsSyncRateLimitError):
        # Keep main quote/predict flow resilient if news source is unavailable.
        return


def _freshness(as_of: datetime) -> str:
    delta_hours = (datetime.utcnow() - as_of).total_seconds() / 3600
    if delta_hours <= 36:
        return "fresh"
    if delta_hours <= 72:
        return "lagging"
    return "stale"


def _to_backtest_response(row) -> BacktestReportResponse:
    return BacktestReportResponse(
        horizon=row.horizon,
        generated_at=row.generated_at,
        report_date=row.report_date.isoformat(),
        window_days=row.window_days,
        model_version=row.model_version,
        metrics=BacktestMetrics(
            accuracy=row.accuracy,
            auc=row.auc,
            precision=row.precision,
            recall=row.recall,
            f1=row.f1,
            annualized_return=row.annualized_return,
            max_drawdown=row.max_drawdown,
            sharpe=row.sharpe,
            sample_size=row.sample_size,
        ),
    )


@router.get("/funds/search", response_model=list[FundItem])
def funds_search(q: str = Query(default=""), db: Session = Depends(get_db)):
    funds = search_funds(db, q)

    # Remote completion path for better first-use experience.
    if q and len(funds) < 10:
        try:
            remote_items = remote_search_funds(q, limit=20)
            upsert_funds(db, remote_items)
            funds = search_funds(db, q)
        except FundSearchRateLimitError as exc:
            raise HTTPException(status_code=429, detail=f"search source throttled: {exc}") from exc
        except FundSearchError:
            pass

    if not funds and q.isdigit() and len(q) == 6:
        try:
            _refresh_news_signal_soft(db, q)
            refresh_fund_data(db, q)
            funds = search_funds(db, q)
        except MarketSyncRateLimitError as exc:
            raise HTTPException(status_code=429, detail=f"quote source throttled: {exc}") from exc
        except MarketSyncError:
            funds = []

    funds = sorted(funds, key=lambda f: (-hot_rank(f.code), f.code))
    return [FundItem(code=f.code, name=f.name, category=f.category) for f in funds]


@router.get("/funds/hot", response_model=list[FundItem])
def funds_hot(db: Session = Depends(get_db)):
    funds = search_funds(db, "")
    funds = sorted(funds, key=lambda f: (-hot_rank(f.code), f.code))
    return [FundItem(code=f.code, name=f.name, category=f.category) for f in funds[:20]]


@router.get("/funds/{code}/quote", response_model=QuoteResponse)
def fund_quote(code: str, db: Session = Depends(get_db)):
    quote = latest_quote(db, code)
    if not quote:
        try:
            _refresh_news_signal_soft(db, code)
            quote = refresh_fund_data(db, code)
        except MarketSyncRateLimitError as exc:
            raise HTTPException(status_code=429, detail=f"quote source throttled: {exc}") from exc
        except MarketSyncError as exc:
            raise HTTPException(status_code=502, detail=f"fund data source unavailable: {exc}") from exc
    return QuoteResponse(
        code=quote.fund_code,
        as_of=quote.as_of,
        data_freshness=_freshness(quote.as_of),
        nav=quote.nav,
        daily_change_pct=quote.daily_change_pct,
        volatility_20d=quote.volatility_20d,
    )


@router.get("/funds/{code}/predict", response_model=PredictResponse)
def fund_predict(code: str, horizon: str = Query(pattern="^(short|mid)$"), db: Session = Depends(get_db)):
    pred = latest_prediction(db, code, horizon)
    if not pred:
        try:
            _refresh_news_signal_soft(db, code)
            refresh_fund_data(db, code)
            pred = latest_prediction(db, code, horizon)
        except MarketSyncRateLimitError as exc:
            raise HTTPException(status_code=429, detail=f"quote source throttled: {exc}") from exc
        except MarketSyncError as exc:
            raise HTTPException(status_code=502, detail=f"fund data source unavailable: {exc}") from exc
    if not pred:
        raise HTTPException(status_code=404, detail="prediction not found")
    return PredictResponse(
        code=pred.fund_code,
        horizon=pred.horizon,
        as_of=pred.as_of,
        data_freshness=_freshness(pred.as_of),
        up_probability=pred.up_probability,
        expected_return_pct=pred.expected_return_pct,
        confidence=pred.confidence,
    )


@router.get("/funds/{code}/explain", response_model=ExplainResponse)
def fund_explain(code: str, horizon: str = Query(pattern="^(short|mid)$"), db: Session = Depends(get_db)):
    pred = latest_prediction(db, code, horizon)
    if not pred:
        try:
            _refresh_news_signal_soft(db, code)
            refresh_fund_data(db, code)
            pred = latest_prediction(db, code, horizon)
        except MarketSyncRateLimitError as exc:
            raise HTTPException(status_code=429, detail=f"quote source throttled: {exc}") from exc
        except MarketSyncError as exc:
            raise HTTPException(status_code=502, detail=f"fund data source unavailable: {exc}") from exc
    if not pred:
        raise HTTPException(status_code=404, detail="prediction not found")
    quote = latest_quote(db, code)
    news_signal = latest_news_signal(db, code)
    market_ctx = latest_market_context(db)
    sentiment_score = news_signal.sentiment_score if news_signal else 0.0
    event_score = news_signal.event_score if news_signal else 0.0
    volume_shock_score = news_signal.volume_shock if news_signal else 0.0
    volatility_20d = quote.volatility_20d if quote else None
    return ExplainResponse(
        code=code,
        horizon=horizon,
        data_freshness=_freshness(pred.as_of),
        confidence_interval_pct=confidence_interval(pred.expected_return_pct, pred.confidence),
        top_factors=explain_features(
            horizon=horizon,
            daily_change_pct=quote.daily_change_pct if quote else None,
            volatility_20d=volatility_20d,
            sentiment_score=sentiment_score,
            event_score=event_score,
            volume_shock_score=volume_shock_score,
            market_score=market_ctx.market_score,
            style_score=market_ctx.style_score,
        ),
        risk_flags=build_risk_flags(
            volatility_20d=volatility_20d,
            confidence=pred.confidence,
            sentiment_score=sentiment_score,
            event_score=event_score,
            volume_shock_score=volume_shock_score,
            market_source_degraded=market_ctx.source_degraded,
        ),
    )


@router.get("/funds/{code}/ai-judgement", response_model=AiJudgementResponse)
def fund_ai_judgement(code: str, horizon: str = Query(pattern="^(short|mid)$"), db: Session = Depends(get_db)):
    try:
        return AiJudgementResponse(**get_ai_second_opinion(db, code, horizon))
    except AiSecondOpinionError as exc:
        if str(exc) != "prediction not found":
            raise HTTPException(status_code=502, detail=f"ai second opinion unavailable: {exc}") from exc

    try:
        _refresh_news_signal_soft(db, code)
        refresh_fund_data(db, code)
    except MarketSyncRateLimitError as exc:
        raise HTTPException(status_code=429, detail=f"quote source throttled: {exc}") from exc
    except MarketSyncError as exc:
        raise HTTPException(status_code=502, detail=f"fund data source unavailable: {exc}") from exc

    try:
        return AiJudgementResponse(**get_ai_second_opinion(db, code, horizon))
    except AiSecondOpinionError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/funds/{code}/kline", response_model=KlineResponse)
def fund_kline(code: str, days: int = Query(default=60, ge=10, le=240)):
    try:
        items = fetch_kline_points(code, days=days)
    except FundDataError as exc:
        raise HTTPException(status_code=502, detail=f"fund data source unavailable: {exc}") from exc
    return KlineResponse(
        code=code,
        is_synthetic=True,
        note="nav_derived_visualization_not_true_ohlc",
        items=[
            KlineItem(ts=i.ts, open=i.open, high=i.high, low=i.low, close=i.close)
            for i in items
        ],
    )


@router.get("/funds/{code}/news-signal", response_model=NewsSignalResponse)
def fund_news_signal(code: str, db: Session = Depends(get_db)):
    row = latest_news_signal(db, code)
    if not row:
        _refresh_news_signal_soft(db, code)
        row = latest_news_signal(db, code)
    if not row:
        return NewsSignalResponse(
            code=code,
            trade_date=datetime.now(tz=UTC).date().isoformat(),
            headline_count=0,
            sentiment_score=0.0,
            event_score=0.0,
            volume_shock=0.0,
            sample_title="暂无新增公告/舆情",
        )
    return NewsSignalResponse(
        code=code,
        trade_date=row.trade_date.isoformat(),
        headline_count=row.headline_count,
        sentiment_score=row.sentiment_score,
        event_score=row.event_score,
        volume_shock=row.volume_shock,
        sample_title=row.sample_title,
    )


@router.post("/funds/{code}/feedback", response_model=FeedbackItem)
def fund_feedback_post(
    code: str,
    payload: FeedbackIn,
    x_user_id: str = Header(default="demo-user", alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    row = add_feedback(
        db,
        user_id=x_user_id,
        fund_code=code,
        horizon=payload.horizon,
        is_helpful=payload.is_helpful,
        score=payload.score,
        comment=payload.comment,
    )
    return FeedbackItem(
        id=row.id,
        user_id=row.user_id,
        fund_code=row.fund_code,
        horizon=row.horizon,
        is_helpful=row.is_helpful == 1,
        score=row.score,
        comment=row.comment,
        pred_as_of=row.pred_as_of,
        created_at=row.created_at,
    )


@router.get("/funds/{code}/feedback/summary", response_model=FeedbackSummaryResponse)
def fund_feedback_summary_get(code: str, horizon: str = Query(pattern="^(short|mid)$"), db: Session = Depends(get_db)):
    return FeedbackSummaryResponse(**feedback_summary(db, fund_code=code, horizon=horizon))


@router.get("/user/watchlist", response_model=list[WatchlistItem])
def watchlist_get(
    x_user_id: str = Header(default="demo-user", alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    rows = get_watchlist(db, x_user_id)
    return [WatchlistItem(user_id=r.user_id, fund_code=r.fund_code) for r in rows]


@router.post("/user/watchlist", response_model=WatchlistItem)
def watchlist_post(
    payload: WatchlistIn,
    x_user_id: str = Header(default="demo-user", alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    row = add_watchlist(db, x_user_id, payload.fund_code)
    return WatchlistItem(user_id=row.user_id, fund_code=row.fund_code)


@router.get("/user/alerts", response_model=list[AlertRuleItem])
def user_alerts_get(
    x_user_id: str = Header(default="demo-user", alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    rows = list_alert_rules(db, user_id=x_user_id)
    return [
        AlertRuleItem(
            id=r.id,
            user_id=r.user_id,
            fund_code=r.fund_code,
            horizon=r.horizon,
            min_up_probability=r.min_up_probability,
            min_confidence=r.min_confidence,
            min_expected_return_pct=r.min_expected_return_pct,
            enabled=r.enabled == 1,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.post("/user/alerts", response_model=AlertRuleItem)
def user_alerts_post(
    payload: AlertRuleIn,
    x_user_id: str = Header(default="demo-user", alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    row = upsert_alert_rule(
        db,
        user_id=x_user_id,
        fund_code=payload.fund_code,
        horizon=payload.horizon,
        min_up_probability=payload.min_up_probability,
        min_confidence=payload.min_confidence,
        min_expected_return_pct=payload.min_expected_return_pct,
        enabled=payload.enabled,
    )
    return AlertRuleItem(
        id=row.id,
        user_id=row.user_id,
        fund_code=row.fund_code,
        horizon=row.horizon,
        min_up_probability=row.min_up_probability,
        min_confidence=row.min_confidence,
        min_expected_return_pct=row.min_expected_return_pct,
        enabled=row.enabled == 1,
        updated_at=row.updated_at,
    )


@router.get("/user/alerts/check", response_model=AlertCheckResponse)
def user_alerts_check(
    x_user_id: str = Header(default="demo-user", alias="X-User-Id"),
    db: Session = Depends(get_db),
):
    hits = check_user_alerts(db, user_id=x_user_id, limit=20)
    return AlertCheckResponse(
        user_id=x_user_id,
        hit_count=len(hits),
        items=[AlertHitItem(**h) for h in hits],
    )


@router.get("/model/health", response_model=ModelHealthResponse)
def model_health():
    return get_model_health()


@router.get("/model/backtest/latest", response_model=BacktestReportResponse)
def model_backtest_latest(
    horizon: str = Query(pattern="^(short|mid)$"),
    db: Session = Depends(get_db),
):
    row = latest_backtest_report(db, horizon)
    if not row:
        row = generate_backtest_report(db, horizon=horizon, window_days=180)
    return _to_backtest_response(row)


@router.get("/model/ab/latest", response_model=list[AbCompareItem])
def model_ab_latest(
    horizon: str = Query(pattern="^(short|mid)$"),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    rows = list_latest_ab_results(db, horizon=horizon, limit=limit)
    return [
        AbCompareItem(
            fund_code=r.fund_code,
            horizon=r.horizon,
            as_of=r.as_of,
            baseline_model_version=r.baseline_model_version,
            candidate_model_version=r.candidate_model_version,
            baseline_up_probability=r.baseline_up_probability,
            candidate_up_probability=r.candidate_up_probability,
            baseline_expected_return_pct=r.baseline_expected_return_pct,
            candidate_expected_return_pct=r.candidate_expected_return_pct,
            actual_return_pct=r.actual_return_pct,
            winner=r.winner,
        )
        for r in rows
    ]


@router.get("/model/ab/summary", response_model=AbSummaryResponse)
def model_ab_summary(
    horizon: str = Query(pattern="^(short|mid)$"),
    db: Session = Depends(get_db),
):
    return AbSummaryResponse(**ab_summary(db, horizon=horizon))


@router.get("/system/data-sources", response_model=DataSourceResponse)
def data_sources():
    return DataSourceResponse(
        sources=[
            DataSourceItem(
                name="Eastmoney pingzhongdata",
                purpose="Fund NAV/Trend",
                url="https://fund.eastmoney.com/pingzhongdata/{fund_code}.js",
            ),
            DataSourceItem(
                name="Eastmoney fundcode_search",
                purpose="Fund Search Autocomplete",
                url="https://fund.eastmoney.com/js/fundcode_search.js",
            ),
            DataSourceItem(
                name="Eastmoney Fund Archives",
                purpose="Fund Announcement Headlines",
                url="https://fundf10.eastmoney.com/FundArchivesDatas.aspx?type=jjgg&code={fund_code}",
            ),
            DataSourceItem(
                name="Eastmoney Index Kline",
                purpose="Market Regime Factors (HS300/CSI500/CHINEXT)",
                url="https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}",
            ),
        ]
    )


@router.get("/system/market-context", response_model=MarketContextResponse)
def system_market_context(db: Session = Depends(get_db)):
    ctx = get_or_refresh_market_context(db)
    return MarketContextResponse(
        market_score=ctx.market_score,
        style_score=ctx.style_score,
        data_freshness=ctx.data_freshness,
        source_degraded=ctx.source_degraded,
    )


@router.get("/internal/cron/daily-refresh")
def cron_daily_refresh(authorization: str | None = Header(default=None, alias="Authorization")):
    _verify_cron_auth(authorization)
    return run_daily_refresh()


@router.get("/internal/cron/weekly-backtest")
def cron_weekly_backtest(authorization: str | None = Header(default=None, alias="Authorization")):
    _verify_cron_auth(authorization)
    return run_weekly_backtest()
