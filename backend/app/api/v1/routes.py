import os

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.fund import (
    DataSourceItem,
    DataSourceResponse,
    ExplainResponse,
    FundItem,
    ModelHealthResponse,
    PredictResponse,
    QuoteResponse,
    WatchlistIn,
    WatchlistItem,
)
from app.services.model_health import get_model_health
from app.services.market_sync import MarketSyncError, MarketSyncRateLimitError, refresh_fund_data
from app.services.predictor import confidence_interval, explain_features
from app.services.fund_search_source import FundSearchError, FundSearchRateLimitError, remote_search_funds
from app.services.fund_sync import upsert_funds
from app.services.hot_funds import hot_rank
from app.services.repository import add_watchlist, get_watchlist, latest_prediction, latest_quote, search_funds
from app.workers.daily_job import run_daily_refresh

router = APIRouter(prefix="/v1")


def _verify_cron_auth(authorization: str | None) -> None:
    expected = os.getenv("CRON_SECRET") or settings.cron_secret
    if not expected:
        raise HTTPException(status_code=503, detail="cron secret is not configured")
    if authorization != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="invalid cron authorization")


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
            refresh_fund_data(db, code)
            pred = latest_prediction(db, code, horizon)
        except MarketSyncRateLimitError as exc:
            raise HTTPException(status_code=429, detail=f"quote source throttled: {exc}") from exc
        except MarketSyncError as exc:
            raise HTTPException(status_code=502, detail=f"fund data source unavailable: {exc}") from exc
    if not pred:
        raise HTTPException(status_code=404, detail="prediction not found")
    return ExplainResponse(
        code=code,
        horizon=horizon,
        confidence_interval_pct=confidence_interval(pred.expected_return_pct, pred.confidence),
        top_factors=explain_features(horizon),
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
        ]
    )


@router.get("/internal/cron/daily-refresh")
def cron_daily_refresh(authorization: str | None = Header(default=None, alias="Authorization")):
    _verify_cron_auth(authorization)
    return run_daily_refresh()
