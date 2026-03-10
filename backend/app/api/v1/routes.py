import os
import json
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import get_current_user_id
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import Prediction, PredictionSnapshot
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
    DataHealthResponse,
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
    PredictionChangeFactor,
    PredictionChangeResponse,
    QuoteResponse,
    UserEventIn,
    UserEventResponse,
    WatchlistIn,
    WatchlistInsightItem,
    WatchlistInsightsResponse,
    WatchlistItem,
    WalkForwardBacktestResponse,
    WeeklyReportResponse,
)
from app.services.alerts_service import check_user_alerts, list_alert_rules, upsert_alert_rule
from app.services.backtest_service import generate_backtest_report
from app.services.data_health_service import build_data_health_summary
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
from app.services.prediction_snapshot_service import latest_snapshot
from app.services.repository import (
    add_watchlist,
    get_watchlist,
    latest_backtest_report,
    latest_news_signal,
    latest_prediction,
    latest_quote,
    search_funds,
)
from app.services.user_ops_service import track_user_event, weekly_user_report, write_api_audit
from app.services.walkforward_service import build_walkforward_report
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


def _audit_safe(
    db: Session,
    *,
    user_id: str,
    endpoint: str,
    method: str,
    status_code: int = 200,
    detail: str | None = None,
) -> None:
    try:
        write_api_audit(
            db,
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            detail=detail,
        )
    except Exception:
        db.rollback()


def _track_event_safe(
    db: Session,
    *,
    user_id: str,
    event_name: str,
    fund_code: str | None = None,
    metadata: dict | None = None,
) -> dict | None:
    try:
        return track_user_event(
            db,
            user_id=user_id,
            event_name=event_name,
            fund_code=fund_code,
            metadata=metadata,
        )
    except Exception:
        db.rollback()
    return None


def _load_snapshot_features(snapshot_row: PredictionSnapshot | None) -> dict:
    if not snapshot_row:
        return {}
    try:
        payload = json.loads(snapshot_row.feature_payload_json)
    except Exception:
        payload = {}
    return payload if isinstance(payload, dict) else {}


def _watchlist_risk_level(*, confidence: float | None, volatility_20d: float | None) -> str:
    if confidence is None:
        return "unknown"
    if confidence < 0.55 or (volatility_20d is not None and volatility_20d >= 2.3):
        return "high"
    if confidence < 0.65 or (volatility_20d is not None and volatility_20d >= 1.6):
        return "medium"
    return "low"


def _watchlist_signal(*, short_up: float | None, mid_up: float | None) -> str:
    if short_up is None and mid_up is None:
        return "数据不足"
    if short_up is not None and mid_up is not None:
        if short_up >= 0.6 and mid_up >= 0.58:
            return "偏多"
        if short_up <= 0.45 and mid_up <= 0.45:
            return "偏空"
        return "震荡"
    value = short_up if short_up is not None else mid_up
    if value is None:
        return "数据不足"
    if value >= 0.6:
        return "偏多"
    if value <= 0.45:
        return "偏空"
    return "震荡"

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
    snapshot = latest_snapshot(db, fund_code=code, horizon=horizon)
    fallback_model = settings.model_short_version if horizon == "short" else settings.model_mid_version
    return PredictResponse(
        code=pred.fund_code,
        horizon=pred.horizon,
        as_of=pred.as_of,
        data_freshness=_freshness(pred.as_of),
        up_probability=pred.up_probability,
        expected_return_pct=pred.expected_return_pct,
        confidence=pred.confidence,
        model_version=snapshot.model_version if snapshot else fallback_model,
        data_source=snapshot.data_source if snapshot else "rule_based",
        snapshot_id=snapshot.snapshot_id if snapshot else None,
    )


@router.get("/funds/{code}/prediction-change", response_model=PredictionChangeResponse)
def fund_prediction_change(code: str, horizon: str = Query(pattern="^(short|mid)$"), db: Session = Depends(get_db)):
    rows = list(
        db.scalars(
            select(Prediction)
            .where(Prediction.fund_code == code, Prediction.horizon == horizon)
            .order_by(Prediction.as_of.desc())
            .limit(2)
        )
    )
    if not rows:
        try:
            _refresh_news_signal_soft(db, code)
            refresh_fund_data(db, code)
        except MarketSyncRateLimitError as exc:
            raise HTTPException(status_code=429, detail=f"quote source throttled: {exc}") from exc
        except MarketSyncError as exc:
            raise HTTPException(status_code=502, detail=f"fund data source unavailable: {exc}") from exc

        rows = list(
            db.scalars(
                select(Prediction)
                .where(Prediction.fund_code == code, Prediction.horizon == horizon)
                .order_by(Prediction.as_of.desc())
                .limit(2)
            )
        )
    if not rows:
        raise HTTPException(status_code=404, detail="prediction not found")

    current = rows[0]
    previous = rows[1] if len(rows) > 1 else None
    current_snapshot = db.scalar(
        select(PredictionSnapshot).where(
            PredictionSnapshot.fund_code == code,
            PredictionSnapshot.horizon == horizon,
            PredictionSnapshot.as_of == current.as_of,
        )
    )
    prev_snapshot = None
    if previous:
        prev_snapshot = db.scalar(
            select(PredictionSnapshot).where(
                PredictionSnapshot.fund_code == code,
                PredictionSnapshot.horizon == horizon,
                PredictionSnapshot.as_of == previous.as_of,
            )
        )

    current_features = _load_snapshot_features(current_snapshot)
    previous_features = _load_snapshot_features(prev_snapshot)
    changed_factors: list[PredictionChangeFactor] = []
    feature_keys = set(current_features.keys()) | set(previous_features.keys())
    for key in feature_keys:
        before_raw = previous_features.get(key)
        after_raw = current_features.get(key)
        try:
            before = float(before_raw) if before_raw is not None else None
            after = float(after_raw) if after_raw is not None else None
        except Exception:
            continue
        if before is None and after is None:
            continue
        delta = round((after or 0.0) - (before or 0.0), 6)
        if abs(delta) < 1e-9:
            continue
        changed_factors.append(
            PredictionChangeFactor(
                name=key,
                before=round(before, 6) if before is not None else None,
                after=round(after, 6) if after is not None else None,
                delta=delta,
            )
        )
    changed_factors = sorted(changed_factors, key=lambda x: abs(x.delta), reverse=True)[:6]

    up_delta = round(float(current.up_probability) - float(previous.up_probability if previous else 0.0), 4)
    exp_delta = round(float(current.expected_return_pct) - float(previous.expected_return_pct if previous else 0.0), 4)
    conf_delta = round(float(current.confidence) - float(previous.confidence if previous else 0.0), 4)

    if previous is None:
        summary = "当前仅有一条预测记录，尚无法形成时序变化结论。"
    elif up_delta >= 0.03 and exp_delta >= 0:
        summary = "与上次相比，短中期信号整体增强。"
    elif up_delta <= -0.03 and exp_delta <= 0:
        summary = "与上次相比，信号明显走弱，需关注风险。"
    else:
        summary = "与上次相比，信号总体平稳，变化有限。"

    return PredictionChangeResponse(
        code=code,
        horizon=horizon,
        current_as_of=current.as_of,
        previous_as_of=previous.as_of if previous else None,
        data_freshness=_freshness(current.as_of),
        up_probability_delta=up_delta,
        expected_return_pct_delta=exp_delta,
        confidence_delta=conf_delta,
        changed_factors=changed_factors,
        summary=summary,
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
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    row = add_feedback(
        db,
        user_id=user_id,
        fund_code=code,
        horizon=payload.horizon,
        is_helpful=payload.is_helpful,
        score=payload.score,
        comment=payload.comment,
    )
    _track_event_safe(
        db,
        user_id=user_id,
        event_name="feedback_submit",
        fund_code=code,
        metadata={"horizon": payload.horizon, "is_helpful": payload.is_helpful, "score": payload.score},
    )
    _audit_safe(
        db,
        user_id=user_id,
        endpoint=f"/v1/funds/{code}/feedback",
        method="POST",
        status_code=200,
        detail=f"horizon={payload.horizon}",
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
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    rows = get_watchlist(db, user_id)
    _track_event_safe(
        db,
        user_id=user_id,
        event_name="watchlist_view",
        metadata={"count": len(rows)},
    )
    _audit_safe(
        db,
        user_id=user_id,
        endpoint="/v1/user/watchlist",
        method="GET",
        status_code=200,
        detail=f"count={len(rows)}",
    )
    return [WatchlistItem(user_id=r.user_id, fund_code=r.fund_code) for r in rows]


@router.post("/user/watchlist", response_model=WatchlistItem)
def watchlist_post(
    payload: WatchlistIn,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    row = add_watchlist(db, user_id, payload.fund_code)
    _track_event_safe(
        db,
        user_id=user_id,
        event_name="watchlist_add",
        fund_code=payload.fund_code,
    )
    _audit_safe(
        db,
        user_id=user_id,
        endpoint="/v1/user/watchlist",
        method="POST",
        status_code=200,
        detail=f"fund_code={payload.fund_code}",
    )
    return WatchlistItem(user_id=row.user_id, fund_code=row.fund_code)


@router.get("/user/watchlist/insights", response_model=WatchlistInsightsResponse)
def watchlist_insights_get(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    rows = get_watchlist(db, user_id)
    items: list[WatchlistInsightItem] = []
    for row in rows:
        short_pred = latest_prediction(db, row.fund_code, "short")
        mid_pred = latest_prediction(db, row.fund_code, "mid")
        quote = latest_quote(db, row.fund_code)
        latest_as_of = max(
            [ts for ts in [short_pred.as_of if short_pred else None, mid_pred.as_of if mid_pred else None] if ts],
            default=None,
        )
        data_freshness = _freshness(latest_as_of) if latest_as_of else "stale"
        short_up = float(short_pred.up_probability) if short_pred else None
        short_conf = float(short_pred.confidence) if short_pred else None
        mid_up = float(mid_pred.up_probability) if mid_pred else None
        mid_conf = float(mid_pred.confidence) if mid_pred else None
        risk_level = _watchlist_risk_level(
            confidence=short_conf if short_conf is not None else mid_conf,
            volatility_20d=quote.volatility_20d if quote else None,
        )
        signal = _watchlist_signal(short_up=short_up, mid_up=mid_up)
        items.append(
            WatchlistInsightItem(
                fund_code=row.fund_code,
                short_up_probability=short_up,
                short_confidence=short_conf,
                mid_up_probability=mid_up,
                mid_confidence=mid_conf,
                data_freshness=data_freshness,
                risk_level=risk_level,
                signal=signal,
            )
        )

    _track_event_safe(
        db,
        user_id=user_id,
        event_name="watchlist_insights_view",
        metadata={"count": len(items)},
    )
    _audit_safe(
        db,
        user_id=user_id,
        endpoint="/v1/user/watchlist/insights",
        method="GET",
        status_code=200,
        detail=f"count={len(items)}",
    )
    return WatchlistInsightsResponse(
        user_id=user_id,
        generated_at=datetime.now(tz=UTC).replace(tzinfo=None),
        items=items,
    )


@router.get("/user/alerts", response_model=list[AlertRuleItem])
def user_alerts_get(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    rows = list_alert_rules(db, user_id=user_id)
    _track_event_safe(
        db,
        user_id=user_id,
        event_name="alerts_view",
        metadata={"count": len(rows)},
    )
    _audit_safe(
        db,
        user_id=user_id,
        endpoint="/v1/user/alerts",
        method="GET",
        status_code=200,
        detail=f"count={len(rows)}",
    )
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
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    row = upsert_alert_rule(
        db,
        user_id=user_id,
        fund_code=payload.fund_code,
        horizon=payload.horizon,
        min_up_probability=payload.min_up_probability,
        min_confidence=payload.min_confidence,
        min_expected_return_pct=payload.min_expected_return_pct,
        enabled=payload.enabled,
    )
    _track_event_safe(
        db,
        user_id=user_id,
        event_name="alerts_upsert",
        fund_code=payload.fund_code,
        metadata={"horizon": payload.horizon, "enabled": payload.enabled},
    )
    _audit_safe(
        db,
        user_id=user_id,
        endpoint="/v1/user/alerts",
        method="POST",
        status_code=200,
        detail=f"fund_code={payload.fund_code},horizon={payload.horizon}",
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
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    hits = check_user_alerts(db, user_id=user_id, limit=20)
    _track_event_safe(
        db,
        user_id=user_id,
        event_name="alerts_check",
        metadata={"hit_count": len(hits)},
    )
    _audit_safe(
        db,
        user_id=user_id,
        endpoint="/v1/user/alerts/check",
        method="GET",
        status_code=200,
        detail=f"hit_count={len(hits)}",
    )
    return AlertCheckResponse(
        user_id=user_id,
        hit_count=len(hits),
        items=[AlertHitItem(**h) for h in hits],
    )


@router.post("/user/events", response_model=UserEventResponse)
def user_event_post(
    payload: UserEventIn,
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    ack = track_user_event(
        db,
        user_id=user_id,
        event_name=payload.event_name,
        fund_code=payload.fund_code,
        metadata=payload.metadata or {},
    )
    _audit_safe(
        db,
        user_id=user_id,
        endpoint="/v1/user/events",
        method="POST",
        status_code=200,
        detail=f"event={payload.event_name}",
    )
    return UserEventResponse(**ack)


@router.get("/user/weekly-report", response_model=WeeklyReportResponse)
def user_weekly_report_get(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    report = weekly_user_report(db, user_id=user_id)
    _audit_safe(
        db,
        user_id=user_id,
        endpoint="/v1/user/weekly-report",
        method="GET",
        status_code=200,
    )
    return WeeklyReportResponse(**report)


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


@router.get("/model/backtest/walkforward", response_model=WalkForwardBacktestResponse)
def model_backtest_walkforward(
    horizon: str = Query(pattern="^(short|mid)$"),
    window_days: int = Query(default=120, ge=60, le=360),
    step_days: int = Query(default=14, ge=7, le=60),
    max_windows: int = Query(default=12, ge=3, le=30),
    db: Session = Depends(get_db),
):
    payload = build_walkforward_report(
        db,
        horizon=horizon,
        window_days=window_days,
        step_days=step_days,
        max_windows=max_windows,
    )
    return WalkForwardBacktestResponse(**payload)


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


@router.get("/system/data-health", response_model=DataHealthResponse)
def system_data_health(db: Session = Depends(get_db)):
    return DataHealthResponse(**build_data_health_summary(db))


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
