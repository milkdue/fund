from dataclasses import dataclass, field
from datetime import datetime
import time

from sqlalchemy import select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models.entities import Fund
from app.services.market_context_service import MarketContextError, MarketContextRateLimitError, refresh_market_indices
from app.services.market_sync import MarketSyncError, refresh_fund_data
from app.services.news_sync import NewsSyncError, NewsSyncRateLimitError, refresh_news_signals_for_code

DEFAULT_CODES = ["110022", "161725", "005827"]
UNSUPPORTED_NAME_MARKERS = ("(后端)", "（后端）")


def _is_supported_fund_name(name: str | None) -> bool:
    normalized = (name or "").strip()
    return normalized != "" and not any(marker in normalized for marker in UNSUPPORTED_NAME_MARKERS)


@dataclass
class _SourcePacer:
    intervals: dict[str, float]
    _last_called_at: dict[str, float] = field(default_factory=dict)

    def wait(self, source: str) -> None:
        interval = self.intervals.get(source, 0.0)
        if interval <= 0:
            return

        now = time.monotonic()
        last_called_at = self._last_called_at.get(source)
        if last_called_at is not None:
            remaining = interval - (now - last_called_at)
            if remaining > 0:
                time.sleep(remaining)

        self._last_called_at[source] = time.monotonic()


def _build_pacer() -> _SourcePacer:
    def per_call_interval(limit_per_min: int) -> float:
        if limit_per_min <= 0:
            return 0.0
        return 60.0 / float(limit_per_min)

    return _SourcePacer(
        intervals={
            "market": per_call_interval(settings.source_market_limit_per_min),
            "news": per_call_interval(settings.source_news_limit_per_min),
            "nav": per_call_interval(settings.source_nav_limit_per_min),
        }
    )


def run_daily_refresh(codes: list[str] | None = None) -> dict:
    started_at = time.monotonic()
    db = SessionLocal()
    target_codes = list(dict.fromkeys(codes or [*DEFAULT_CODES]))
    pacer = _build_pacer()
    skipped_unsupported_codes: list[str] = []

    try:
        if codes is None:
            existing_funds = list(db.scalars(select(Fund)))
            for fund in existing_funds:
                if not _is_supported_fund_name(fund.name):
                    skipped_unsupported_codes.append(fund.code)
                    continue
                if fund.code not in target_codes:
                    target_codes.append(fund.code)
        else:
            filtered_codes: list[str] = []
            for code in target_codes:
                fund = db.scalar(select(Fund).where(Fund.code == code))
                if fund and not _is_supported_fund_name(fund.name):
                    skipped_unsupported_codes.append(code)
                    continue
                filtered_codes.append(code)
            target_codes = filtered_codes

        market_status = "ok"
        try:
            pacer.wait("market")
            refresh_market_indices(db)
        except (MarketContextError, MarketContextRateLimitError):
            market_status = "degraded"

        success = 0
        failed: list[str] = []
        news_success = 0
        news_failed: list[str] = []
        for code in target_codes:
            try:
                pacer.wait("news")
                refresh_news_signals_for_code(db, code)
                news_success += 1
            except (NewsSyncError, NewsSyncRateLimitError):
                news_failed.append(code)

            try:
                pacer.wait("nav")
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
        "target_code_count": len(target_codes),
        "market_status": market_status,
        "success_count": success,
        "failed_codes": failed,
        "news_success_count": news_success,
        "news_failed_codes": news_failed,
        "skipped_unsupported_codes": skipped_unsupported_codes,
        "elapsed_seconds": round(time.monotonic() - started_at, 2),
    }


if __name__ == "__main__":
    print(run_daily_refresh())
