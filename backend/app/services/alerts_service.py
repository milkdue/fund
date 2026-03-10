from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AlertEvent, AlertRule, Prediction


def upsert_alert_rule(
    db: Session,
    *,
    user_id: str,
    fund_code: str,
    horizon: str,
    min_up_probability: float,
    min_confidence: float,
    min_expected_return_pct: float,
    enabled: bool,
) -> AlertRule:
    row = db.scalar(
        select(AlertRule).where(
            AlertRule.user_id == user_id,
            AlertRule.fund_code == fund_code,
            AlertRule.horizon == horizon,
        )
    )
    if not row:
        row = AlertRule(
            user_id=user_id,
            fund_code=fund_code,
            horizon=horizon,
        )
        db.add(row)
    row.min_up_probability = max(0.0, min(min_up_probability, 1.0))
    row.min_confidence = max(0.0, min(min_confidence, 1.0))
    row.min_expected_return_pct = min_expected_return_pct
    row.enabled = 1 if enabled else 0
    db.commit()
    db.refresh(row)
    return row


def list_alert_rules(db: Session, *, user_id: str) -> list[AlertRule]:
    return list(
        db.scalars(
            select(AlertRule)
            .where(AlertRule.user_id == user_id)
            .order_by(AlertRule.updated_at.desc())
        )
    )


def _is_triggered(rule: AlertRule, pred: Prediction) -> bool:
    if rule.enabled != 1:
        return False
    return (
        pred.up_probability >= rule.min_up_probability
        and pred.confidence >= rule.min_confidence
        and pred.expected_return_pct >= rule.min_expected_return_pct
    )


def evaluate_and_record_alert_events(db: Session, *, fund_code: str, horizon: str, prediction_id: int) -> list[AlertEvent]:
    pred = db.scalar(select(Prediction).where(Prediction.id == prediction_id))
    if not pred:
        return []
    rules = list(
        db.scalars(
            select(AlertRule).where(
                AlertRule.fund_code == fund_code,
                AlertRule.horizon == horizon,
                AlertRule.enabled == 1,
            )
        )
    )
    created: list[AlertEvent] = []
    for rule in rules:
        if not _is_triggered(rule, pred):
            continue
        existing = db.scalar(
            select(AlertEvent).where(
                AlertEvent.rule_id == rule.id,
                AlertEvent.prediction_id == pred.id,
            )
        )
        if existing:
            continue
        message = (
            f"{rule.fund_code} {rule.horizon}: 概率{pred.up_probability:.2f}, "
            f"置信度{pred.confidence:.2f}, 预期{pred.expected_return_pct:.2f}%"
        )
        event = AlertEvent(
            rule_id=rule.id,
            prediction_id=pred.id,
            user_id=rule.user_id,
            fund_code=rule.fund_code,
            horizon=rule.horizon,
            message=message[:256],
        )
        db.add(event)
        created.append(event)
    if created:
        db.flush()
    return created


def check_user_alerts(db: Session, *, user_id: str, limit: int = 20) -> list[dict]:
    rules = list(
        db.scalars(
            select(AlertRule)
            .where(AlertRule.user_id == user_id, AlertRule.enabled == 1)
            .order_by(AlertRule.updated_at.desc())
            .limit(200)
        )
    )
    hits: list[dict] = []
    for rule in rules:
        pred = db.scalar(
            select(Prediction)
            .where(Prediction.fund_code == rule.fund_code, Prediction.horizon == rule.horizon)
            .order_by(Prediction.as_of.desc())
            .limit(1)
        )
        if not pred or not _is_triggered(rule, pred):
            continue
        hits.append(
            {
                "rule_id": rule.id,
                "fund_code": rule.fund_code,
                "horizon": rule.horizon,
                "up_probability": pred.up_probability,
                "confidence": pred.confidence,
                "expected_return_pct": pred.expected_return_pct,
                "as_of": pred.as_of,
                "message": f"{rule.fund_code} 触发阈值提醒",
            }
        )
        if len(hits) >= limit:
            break
    return hits
