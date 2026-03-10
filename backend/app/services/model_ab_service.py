from __future__ import annotations

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.entities import PredictionABResult


def list_latest_ab_results(db: Session, *, horizon: str, limit: int = 20) -> list[PredictionABResult]:
    return list(
        db.scalars(
            select(PredictionABResult)
            .where(PredictionABResult.horizon == horizon)
            .order_by(PredictionABResult.as_of.desc(), PredictionABResult.created_at.desc())
            .limit(max(1, min(limit, 100)))
        )
    )


def ab_summary(db: Session, *, horizon: str) -> dict:
    rows = db.execute(
        select(
            func.count(PredictionABResult.id),
            func.sum(case((PredictionABResult.winner == "candidate", 1), else_=0)),
            func.sum(case((PredictionABResult.winner == "baseline", 1), else_=0)),
            func.sum(case((PredictionABResult.winner == "tie", 1), else_=0)),
            func.max(PredictionABResult.baseline_model_version),
            func.max(PredictionABResult.candidate_model_version),
        ).where(PredictionABResult.horizon == horizon)
    ).one()

    total = int(rows[0] or 0)
    cand = int(rows[1] or 0)
    base = int(rows[2] or 0)
    tie = int(rows[3] or 0)
    return {
        "horizon": horizon,
        "baseline_model_version": rows[4] or "unknown",
        "candidate_model_version": rows[5] or "unknown",
        "sample_size": total,
        "candidate_win_rate": round(cand / total, 4) if total else 0.0,
        "baseline_win_rate": round(base / total, 4) if total else 0.0,
        "tie_rate": round(tie / total, 4) if total else 0.0,
    }
