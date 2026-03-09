from datetime import datetime

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.entities import Fund
from app.services.market_sync import MarketSyncError, refresh_fund_data

DEFAULT_CODES = ["110022", "161725", "005827"]


def run_daily_refresh(codes: list[str] | None = None) -> dict:
    db = SessionLocal()
    target_codes = codes or [*DEFAULT_CODES]

    try:
        existing_codes = list(db.scalars(select(Fund.code)))
        for code in existing_codes:
            if code not in target_codes:
                target_codes.append(code)

        success = 0
        failed: list[str] = []
        for code in target_codes:
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
        "success_count": success,
        "failed_codes": failed,
    }


if __name__ == "__main__":
    print(run_daily_refresh())
