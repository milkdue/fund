from datetime import UTC, datetime

from app.db.session import SessionLocal
from app.services.backtest_service import generate_backtest_report

HORIZONS = ["short", "mid"]


def run_weekly_backtest() -> dict:
    db = SessionLocal()
    try:
        reports = []
        for horizon in HORIZONS:
            row = generate_backtest_report(db, horizon=horizon, window_days=180)
            reports.append(
                {
                    "horizon": row.horizon,
                    "report_date": row.report_date.isoformat(),
                    "sample_size": row.sample_size,
                    "accuracy": row.accuracy,
                    "auc": row.auc,
                    "f1": row.f1,
                    "annualized_return": row.annualized_return,
                    "max_drawdown": row.max_drawdown,
                    "sharpe": row.sharpe,
                }
            )
    finally:
        db.close()

    return {
        "job": "weekly_backtest",
        "status": "ok",
        "run_at": datetime.now(tz=UTC).isoformat(),
        "reports": reports,
    }
