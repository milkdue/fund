import os
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.fund import (
    DataSourceItem,
    DataSourceResponse,
    ExplainResponse,
    KlineItem,
    KlineResponse,
    FundItem,
    ModelHealthResponse,
    NewsSignalResponse,
    PredictResponse,
    QuoteResponse,
    WatchlistIn,
    WatchlistItem,
)
from app.services.model_health import get_model_health
from app.services.market_sync import MarketSyncError, MarketSyncRateLimitError, refresh_fund_data
from app.services.news_sync import NewsSyncError, NewsSyncRateLimitError, refresh_news_signals_for_code
from app.services.predictor import confidence_interval, explain_features
from app.services.fund_search_source import FundSearchError, FundSearchRateLimitError, remote_search_funds
from app.services.fund_data_source import FundDataError, fetch_kline_points
from app.services.fund_sync import upsert_funds
from app.services.hot_funds import hot_rank
from app.services.repository import (
    add_watchlist,
    get_watchlist,
    latest_news_signal,
    latest_prediction,
    latest_quote,
    search_funds,
)
from app.workers.daily_job import run_daily_refresh

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
    return ExplainResponse(
        code=code,
        horizon=horizon,
        confidence_interval_pct=confidence_interval(pred.expected_return_pct, pred.confidence),
        top_factors=explain_features(
            horizon=horizon,
            daily_change_pct=quote.daily_change_pct if quote else None,
            volatility_20d=quote.volatility_20d if quote else None,
            sentiment_score=news_signal.sentiment_score if news_signal else 0.0,
            event_score=news_signal.event_score if news_signal else 0.0,
            volume_shock_score=news_signal.volume_shock if news_signal else 0.0,
        ),
    )


@router.get("/funds/{code}/kline", response_model=KlineResponse)
def fund_kline(code: str, days: int = Query(default=60, ge=10, le=240)):
    try:
        items = fetch_kline_points(code, days=days)
    except FundDataError as exc:
        raise HTTPException(status_code=502, detail=f"fund data source unavailable: {exc}") from exc
    return KlineResponse(
        code=code,
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


@router.get("/model/health", response_model=ModelHealthResponse)
def model_health():
    return get_model_health()


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
        ]
    )


@router.get("/internal/cron/daily-refresh")
def cron_daily_refresh(authorization: str | None = Header(default=None, alias="Authorization")):
    _verify_cron_auth(authorization)
    return run_daily_refresh()
