from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import AlertEvent, AlertRule, Prediction
from app.services.ai_second_opinion import peek_ai_second_opinion
from app.services.market_context_service import get_or_refresh_market_context
from app.services.predictor import build_risk_flags
from app.services.repository import latest_news_signal, latest_quote
from app.services.score_service import build_prediction_scorecard


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


def _freshness(as_of) -> str:
    from app.services.time_utils import shanghai_now_naive

    delta_hours = (shanghai_now_naive() - as_of).total_seconds() / 3600
    if delta_hours <= 36:
        return "fresh"
    if delta_hours <= 72:
        return "lagging"
    return "stale"


def _build_alert_context(db: Session, *, pred: Prediction) -> tuple[object | None, object | None, object, dict | None, list[str], object]:
    quote = latest_quote(db, pred.fund_code)
    news_signal = latest_news_signal(db, pred.fund_code)
    market_ctx = get_or_refresh_market_context(db)
    risk_flags = build_risk_flags(
        volatility_20d=quote.volatility_20d if quote else None,
        confidence=pred.confidence,
        sentiment_score=news_signal.sentiment_score if news_signal else 0.0,
        event_score=news_signal.event_score if news_signal else 0.0,
        volume_shock_score=news_signal.volume_shock if news_signal else 0.0,
        market_source_degraded=market_ctx.source_degraded,
    )
    ai_payload = peek_ai_second_opinion(db, pred.fund_code, pred.horizon, pred.as_of)
    scorecard = build_prediction_scorecard(
        horizon=pred.horizon,
        up_probability=float(pred.up_probability),
        expected_return_pct=float(pred.expected_return_pct),
        confidence=float(pred.confidence),
        data_freshness=_freshness(pred.as_of),
        volatility_20d=quote.volatility_20d if quote else None,
        market_score=market_ctx.market_score,
        style_score=market_ctx.style_score,
        sentiment_score=news_signal.sentiment_score if news_signal else 0.0,
        event_score=news_signal.event_score if news_signal else 0.0,
        volume_shock_score=news_signal.volume_shock if news_signal else 0.0,
        risk_flags=risk_flags,
        market_source_degraded=market_ctx.source_degraded,
        ai_payload=ai_payload,
    )
    return quote, news_signal, market_ctx, ai_payload, risk_flags, scorecard


def _classify_alert_message(
    *,
    rule: AlertRule,
    pred: Prediction,
    previous: Prediction | None,
    quote,
    market_ctx,
    ai_payload: dict | None,
    risk_flags: list[str],
    scorecard,
) -> str | None:
    threshold_hit = _is_triggered(rule, pred)
    freshness = _freshness(pred.as_of)
    agreement = (ai_payload or {}).get("agreement_with_model", "")
    bad_flags = [flag for flag in risk_flags if flag != "风险整体可控"]
    prob_delta = float(pred.up_probability) - float(previous.up_probability if previous else 0.0)
    exp_delta = float(pred.expected_return_pct) - float(previous.expected_return_pct if previous else 0.0)

    if freshness != "fresh" or market_ctx.source_degraded or scorecard.components[-1].score < 45:
        return (
            f"[数据风险提醒] {rule.fund_code} {rule.horizon} 数据新鲜度 {freshness}，"
            f"可信度分 {scorecard.components[-1].score}，建议等待下一轮刷新。"
        )[:256]

    if str(agreement).lower() == "disagree":
        return (
            f"[分歧提醒] {rule.fund_code} {rule.horizon} 量化信号 {scorecard.signal_bias}，"
            f"但 AI 第二意见存在分歧，当前仅建议观察。"
        )[:256]

    if scorecard.risk_score < 40 or any(flag in {"高波动风险", "舆情偏负面", "公告事件偏利空"} for flag in bad_flags):
        risk_hint = "、".join(bad_flags[:2]) if bad_flags else "风险分偏低"
        return (
            f"[风险提醒] {rule.fund_code} {rule.horizon} 风险分 {scorecard.risk_score}，"
            f"{risk_hint}，建议降低仓位或暂缓决策。"
        )[:256]

    if threshold_hit and previous and (prob_delta >= 0.05 or exp_delta >= 0.8):
        return (
            f"[升级提醒] {rule.fund_code} {rule.horizon} 综合评分 {scorecard.total_score}，"
            f"上涨概率较上次提升 {prob_delta * 100:.0f}pt，信号增强。"
        )[:256]

    if threshold_hit and scorecard.total_score >= 75 and scorecard.risk_score >= 55:
        return (
            f"[入选提醒] {rule.fund_code} {rule.horizon} 综合评分 {scorecard.total_score}，"
            f"行动标签 {scorecard.action_label}，上涨概率 {pred.up_probability * 100:.0f}%。"
        )[:256]

    if threshold_hit:
        return (
            f"[阈值提醒] {rule.fund_code} {rule.horizon} 已触发提醒阈值，"
            f"综合评分 {scorecard.total_score}，风险分 {scorecard.risk_score}。"
        )[:256]

    return None


def evaluate_and_record_alert_events(db: Session, *, fund_code: str, horizon: str, prediction_id: int) -> list[AlertEvent]:
    pred = db.scalar(select(Prediction).where(Prediction.id == prediction_id))
    if not pred:
        return []
    previous = db.scalar(
        select(Prediction)
        .where(
            Prediction.fund_code == fund_code,
            Prediction.horizon == horizon,
            Prediction.as_of < pred.as_of,
        )
        .order_by(Prediction.as_of.desc())
        .limit(1)
    )
    quote, _, market_ctx, ai_payload, risk_flags, scorecard = _build_alert_context(db, pred=pred)
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
        message = _classify_alert_message(
            rule=rule,
            pred=pred,
            previous=previous,
            quote=quote,
            market_ctx=market_ctx,
            ai_payload=ai_payload,
            risk_flags=risk_flags,
            scorecard=scorecard,
        )
        if not message:
            continue
        existing = db.scalar(
            select(AlertEvent).where(
                AlertEvent.rule_id == rule.id,
                AlertEvent.prediction_id == pred.id,
            )
        )
        if existing:
            continue
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
        if not pred:
            continue
        previous = db.scalar(
            select(Prediction)
            .where(
                Prediction.fund_code == rule.fund_code,
                Prediction.horizon == rule.horizon,
                Prediction.as_of < pred.as_of,
            )
            .order_by(Prediction.as_of.desc())
            .limit(1)
        )
        quote, _, market_ctx, ai_payload, risk_flags, scorecard = _build_alert_context(db, pred=pred)
        message = _classify_alert_message(
            rule=rule,
            pred=pred,
            previous=previous,
            quote=quote,
            market_ctx=market_ctx,
            ai_payload=ai_payload,
            risk_flags=risk_flags,
            scorecard=scorecard,
        )
        if not message:
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
                "message": message,
            }
        )
        if len(hits) >= limit:
            break
    return hits


def list_alert_events(db: Session, *, user_id: str, limit: int = 50) -> list[AlertEvent]:
    return list(
        db.scalars(
            select(AlertEvent)
            .where(AlertEvent.user_id == user_id)
            .order_by(AlertEvent.created_at.desc(), AlertEvent.id.desc())
            .limit(max(1, min(limit, 200)))
        )
    )
