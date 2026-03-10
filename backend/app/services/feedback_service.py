from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.entities import Prediction, PredictionFeedback


def add_feedback(
    db: Session,
    *,
    user_id: str,
    fund_code: str,
    horizon: str,
    is_helpful: bool,
    score: int,
    comment: str | None,
) -> PredictionFeedback:
    latest_pred = db.scalar(
        select(Prediction)
        .where(Prediction.fund_code == fund_code, Prediction.horizon == horizon)
        .order_by(Prediction.as_of.desc())
        .limit(1)
    )
    row = PredictionFeedback(
        user_id=user_id,
        fund_code=fund_code,
        horizon=horizon,
        is_helpful=1 if is_helpful else 0,
        score=max(1, min(score, 5)),
        comment=(comment or "").strip()[:512] or None,
        pred_as_of=latest_pred.as_of if latest_pred else None,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def feedback_summary(db: Session, *, fund_code: str, horizon: str) -> dict:
    rows = db.execute(
        select(
            func.count(PredictionFeedback.id),
            func.sum(PredictionFeedback.is_helpful),
            func.avg(PredictionFeedback.score),
        ).where(PredictionFeedback.fund_code == fund_code, PredictionFeedback.horizon == horizon)
    ).one()
    total = int(rows[0] or 0)
    helpful = int(rows[1] or 0)
    avg_score = float(rows[2] or 0.0)
    helpful_rate = round(helpful / total, 4) if total else 0.0
    return {
        "fund_code": fund_code,
        "horizon": horizon,
        "total": total,
        "helpful": helpful,
        "helpful_rate": helpful_rate,
        "avg_score": round(avg_score, 4),
    }
