from __future__ import annotations

import json
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import AlertEvent, ApiAuditLog, PredictionFeedback, UserEvent


def write_api_audit(
    db: Session,
    *,
    user_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    detail: str | None = None,
) -> None:
    if not settings.auth_audit_enabled:
        return
    ApiAuditLog.__table__.create(bind=db.get_bind(), checkfirst=True)
    row = ApiAuditLog(
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        detail=(detail or "")[:512] or None,
    )
    db.add(row)
    db.commit()


def track_user_event(
    db: Session,
    *,
    user_id: str,
    event_name: str,
    fund_code: str | None = None,
    metadata: dict | None = None,
) -> dict:
    UserEvent.__table__.create(bind=db.get_bind(), checkfirst=True)
    event_day = datetime.now(tz=UTC).date()
    existing = db.scalar(
        select(UserEvent).where(
            UserEvent.user_id == user_id,
            UserEvent.event_name == event_name,
            UserEvent.event_day == event_day,
            UserEvent.fund_code == fund_code,
        )
    )
    payload_json = json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)
    if existing:
        existing.count += 1
        existing.metadata_json = payload_json
        db.commit()
        return {"id": existing.id, "count": existing.count, "event_day": existing.event_day.isoformat()}

    row = UserEvent(
        user_id=user_id,
        event_name=event_name,
        fund_code=fund_code,
        event_day=event_day,
        metadata_json=payload_json,
        count=1,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"id": row.id, "count": row.count, "event_day": row.event_day.isoformat()}


def weekly_user_report(db: Session, *, user_id: str) -> dict:
    UserEvent.__table__.create(bind=db.get_bind(), checkfirst=True)
    ApiAuditLog.__table__.create(bind=db.get_bind(), checkfirst=True)
    from_day = date.today() - timedelta(days=6)

    event_rows = list(
        db.execute(
            select(UserEvent.event_name, func.sum(UserEvent.count))
            .where(UserEvent.user_id == user_id, UserEvent.event_day >= from_day)
            .group_by(UserEvent.event_name)
        )
    )
    event_counts = {name: int(total or 0) for name, total in event_rows}

    audit_total = int(
        db.scalar(
            select(func.count(ApiAuditLog.id)).where(
                ApiAuditLog.user_id == user_id,
                ApiAuditLog.created_at >= datetime.combine(from_day, datetime.min.time()),
            )
        )
        or 0
    )

    feedback_total = int(
        db.scalar(
            select(func.count(PredictionFeedback.id)).where(
                PredictionFeedback.user_id == user_id,
                PredictionFeedback.created_at >= datetime.combine(from_day, datetime.min.time()),
            )
        )
        or 0
    )
    feedback_helpful = int(
        db.scalar(
            select(func.count(PredictionFeedback.id)).where(
                PredictionFeedback.user_id == user_id,
                PredictionFeedback.created_at >= datetime.combine(from_day, datetime.min.time()),
                PredictionFeedback.is_helpful == 1,
            )
        )
        or 0
    )

    alert_hits = int(
        db.scalar(
            select(func.count(AlertEvent.id)).where(
                AlertEvent.user_id == user_id,
                AlertEvent.created_at >= datetime.combine(from_day, datetime.min.time()),
            )
        )
        or 0
    )

    helpful_rate = round(feedback_helpful / feedback_total, 4) if feedback_total else 0.0
    return {
        "user_id": user_id,
        "from_date": from_day.isoformat(),
        "to_date": date.today().isoformat(),
        "audit_requests": audit_total,
        "event_counts": event_counts,
        "feedback_total": feedback_total,
        "feedback_helpful_rate": helpful_rate,
        "alert_hits": alert_hits,
    }
