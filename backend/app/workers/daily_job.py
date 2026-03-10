from datetime import datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import Fund
from app.services.market_context_service import MarketContextError, MarketContextRateLimitError, refresh_market_indices
from app.services.market_sync import MarketSyncError, refresh_fund_data
from app.services.news_sync import NewsSyncError, NewsSyncRateLimitError, refresh_news_signals_for_code

DEFAULT_CODES = ["110022", "161725", "005827"]


def run_daily_refresh(codes: list[str] | None = None) -> dict:
    db = SessionLocal()
    target_codes = codes or [*DEFAULT_CODES]

    try:
        existing_codes = list(db.scalars(select(Fund.code)))
        for code in existing_codes:
            if code not in target_codes:
                target_codes.append(code)

        market_status = "ok"
        try:
            refresh_market_indices(db)
        except (MarketContextError, MarketContextRateLimitError):
            market_status = "degraded"

        success = 0
        failed: list[str] = []
        news_success = 0
        news_failed: list[str] = []
        for code in target_codes:
            try:
                refresh_news_signals_for_code(db, code)
                news_success += 1
            except (NewsSyncError, NewsSyncRateLimitError):
                news_failed.append(code)

            try:
                refresh_fund_data(db, code)
                success += 1
            except MarketSyncError:
                failed.append(code)
    finally:
        db.close()

    coverage = round(success / len(target_codes), 4) if target_codes else 0.0
    return {
        "job": "daily_refresh",
        "status": "ok" if not failed else "partial",
        "run_at": datetime.utcnow().isoformat(),
        "coverage_rate": coverage,
        "market_status": market_status,
        "success_count": success,
        "failed_codes": failed,
        "news_success_count": news_success,
        "news_failed_codes": news_failed,
    }


if __name__ == "__main__":
    print(run_daily_refresh())
