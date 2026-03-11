from __future__ import annotations

import json
import re
from datetime import UTC, date, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import AiJudgementCache, AiUsageDaily, Fund
from app.services.market_context_service import get_or_refresh_market_context
from app.services.predictor import build_risk_flags, explain_features
from app.services.repository import latest_backtest_report, latest_news_signal, latest_prediction, latest_quote


class AiSecondOpinionError(Exception):
    pass


NON_COMPLIANT_PATTERNS = [
    re.compile(r"(保本|稳赚|稳赚不赔|必涨|翻倍|躺赚|无风险)"),
    re.compile(r"(guarantee|guaranteed|sure\s*win|risk[-\s]*free|100\s*%)", re.I),
]


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _freshness(as_of: datetime) -> str:
    delta_hours = (datetime.utcnow() - as_of).total_seconds() / 3600
    if delta_hours <= 36:
        return "fresh"
    if delta_hours <= 72:
        return "lagging"
    return "stale"


def _parse_json_text(raw_text: str) -> dict:
    text = (raw_text or "").strip()
    if not text:
        return {}
    text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        loaded = json.loads(text)
        return loaded if isinstance(loaded, dict) else {}
    except Exception:
        return {}


def _trend_from_quant(expected_return_pct: float) -> str:
    if expected_return_pct >= 0.5:
        return "up"
    if expected_return_pct <= -0.5:
        return "down"
    return "sideways"


def _safe_list(raw_value, fallback: list[str]) -> list[str]:
    if not isinstance(raw_value, list):
        return fallback
    values = [str(i).strip() for i in raw_value if str(i).strip()]
    if not values:
        return fallback
    return values[:6]


def _contains_non_compliant(text: str) -> bool:
    content = (text or "").strip()
    if not content:
        return False
    return any(p.search(content) for p in NON_COMPLIANT_PATTERNS)


def _cache_model_name() -> str:
    if settings.gemini_enabled and settings.gemini_api_key:
        return settings.gemini_model
    return "fallback"


def _fallback_payload(
    *,
    code: str,
    horizon: str,
    as_of: datetime,
    data_freshness: str,
    up_probability: float,
    expected_return_pct: float,
    confidence: float,
    factors: list,
    risk_flags: list[str],
) -> dict:
    trend = _trend_from_quant(expected_return_pct)
    strength = int(_clamp(abs(expected_return_pct) * 18 + confidence * 25, 5, 95))
    conf_adj = -0.03 if "置信度偏低" in risk_flags else 0.0
    adjusted_prob = _clamp(up_probability + conf_adj, 0.05, 0.95)
    reasons = [f"{f.name}({f.contribution:+.2f})" for f in factors[:3]] or ["量化信号为主"]
    warnings = risk_flags[:4] if risk_flags else ["请结合市场波动谨慎判断"]

    return {
        "code": code,
        "horizon": horizon,
        "as_of": as_of,
        "data_freshness": data_freshness,
        "trend": trend,
        "trend_strength": strength,
        "agreement_with_model": "agree",
        "key_reasons": reasons,
        "risk_warnings": warnings,
        "confidence_adjustment": round(conf_adj, 4),
        "adjusted_up_probability": round(adjusted_prob, 4),
        "summary": "AI第二意见（规则降级）认为可参考量化结果，但需关注风险标签。",
        "provider": "fallback-rule",
        "model": "fallback",
    }


def _normalize_payload(
    *,
    parsed: dict,
    code: str,
    horizon: str,
    as_of: datetime,
    data_freshness: str,
    up_probability: float,
    expected_return_pct: float,
    factors: list,
    risk_flags: list[str],
) -> dict:
    trend = str(parsed.get("trend", "")).strip().lower()
    if trend not in {"up", "down", "sideways"}:
        trend = _trend_from_quant(expected_return_pct)

    agreement = str(parsed.get("agreement_with_model", "")).strip().lower()
    if agreement not in {"agree", "partial", "disagree"}:
        agreement = "partial"

    trend_strength_raw = parsed.get("trend_strength", 50)
    try:
        trend_strength = int(trend_strength_raw)
    except Exception:
        trend_strength = 50
    trend_strength = int(_clamp(trend_strength, 0, 100))

    fallback_reasons = [f"{f.name}({f.contribution:+.2f})" for f in factors[:3]] or ["量化因子综合信号"]
    key_reasons = _safe_list(parsed.get("key_reasons"), fallback_reasons)
    risk_warnings = _safe_list(parsed.get("risk_warnings"), risk_flags or ["请结合风险标签谨慎判断"])

    try:
        conf_adj = float(parsed.get("confidence_adjustment", 0.0))
    except Exception:
        conf_adj = 0.0
    conf_adj = round(_clamp(conf_adj, -0.25, 0.25), 4)

    try:
        adjusted_prob = float(parsed.get("adjusted_up_probability"))
    except Exception:
        adjusted_prob = up_probability + conf_adj
    adjusted_prob = round(_clamp(adjusted_prob, 0.0, 1.0), 4)

    summary = str(parsed.get("summary", "")).strip()
    if not summary:
        summary = "AI第二意见已生成，请结合量化预测与风险提示综合判断。"
    summary = summary[:300]

    return {
        "code": code,
        "horizon": horizon,
        "as_of": as_of,
        "data_freshness": data_freshness,
        "trend": trend,
        "trend_strength": trend_strength,
        "agreement_with_model": agreement,
        "key_reasons": key_reasons,
        "risk_warnings": risk_warnings,
        "confidence_adjustment": conf_adj,
        "adjusted_up_probability": adjusted_prob,
        "summary": summary,
        "provider": "gemini",
        "model": settings.gemini_model,
    }


def _validate_gemini_payload(parsed: dict) -> None:
    required_fields = {
        "trend",
        "trend_strength",
        "agreement_with_model",
        "key_reasons",
        "risk_warnings",
        "confidence_adjustment",
        "adjusted_up_probability",
        "summary",
    }
    missing = [k for k in required_fields if k not in parsed]
    if missing:
        raise AiSecondOpinionError(f"gemini json missing fields: {','.join(sorted(missing))}")
    if not isinstance(parsed.get("key_reasons"), list) or not isinstance(parsed.get("risk_warnings"), list):
        raise AiSecondOpinionError("gemini json list fields are invalid")


def _apply_compliance_filter(payload: dict) -> dict:
    if not settings.gemini_compliance_filter_enabled:
        return payload

    updated = dict(payload)
    reasons = [str(i).strip()[:120] for i in updated.get("key_reasons", []) if str(i).strip()]
    warnings = [str(i).strip()[:120] for i in updated.get("risk_warnings", []) if str(i).strip()]
    summary = str(updated.get("summary", "")).strip()[:300]

    flagged = False
    if _contains_non_compliant(summary):
        flagged = True
        summary = "AI第二意见已触发合规降级：输出仅供学习研究参考，不构成投资建议。"

    clean_reasons: list[str] = []
    for item in reasons:
        if _contains_non_compliant(item):
            flagged = True
            continue
        clean_reasons.append(item)
    if not clean_reasons:
        clean_reasons = ["综合量化与市场因子后，给出非确定性参考意见"]

    clean_warnings: list[str] = []
    for item in warnings:
        if _contains_non_compliant(item):
            flagged = True
            continue
        clean_warnings.append(item)
    if flagged:
        clean_warnings.insert(0, "检测到确定性措辞，结果已按合规要求自动降级。")
    if not clean_warnings:
        clean_warnings = ["市场存在不确定性，请谨慎判断并控制风险。"]

    updated["summary"] = summary or "AI第二意见已生成，请结合量化预测与风险提示综合判断。"
    updated["key_reasons"] = list(dict.fromkeys(clean_reasons))[:6]
    updated["risk_warnings"] = list(dict.fromkeys(clean_warnings))[:6]
    return updated


def _today_utc() -> date:
    return datetime.now(tz=UTC).date()


def _consume_ai_daily_budget(db: Session) -> bool:
    if settings.gemini_daily_budget_calls <= 0:
        return False

    AiUsageDaily.__table__.create(bind=db.get_bind(), checkfirst=True)
    usage_date = _today_utc()
    row = db.scalar(
        select(AiUsageDaily).where(
            AiUsageDaily.usage_date == usage_date,
            AiUsageDaily.provider == "gemini",
            AiUsageDaily.model == settings.gemini_model,
        )
    )
    used = int(row.call_count if row else 0)
    if used >= settings.gemini_daily_budget_calls:
        return False

    if row:
        row.call_count = used + 1
    else:
        db.add(
            AiUsageDaily(
                usage_date=usage_date,
                provider="gemini",
                model=settings.gemini_model,
                call_count=1,
            )
        )
    db.flush()
    return True


def _call_gemini(context: dict) -> tuple[dict, str]:
    if not settings.gemini_enabled or not settings.gemini_api_key:
        raise AiSecondOpinionError("gemini is not enabled")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent"
    prompt = (
        "你是基金投资辅助系统的二级判断引擎。"
        "请基于输入数据给出短期或中期趋势判断。"
        "必须仅返回 JSON，不要 markdown，不要额外解释。"
        "JSON字段必须包含："
        "trend(up|down|sideways), trend_strength(0-100), agreement_with_model(agree|partial|disagree), "
        "key_reasons(string[]), risk_warnings(string[]), confidence_adjustment(-0.25~0.25), "
        "adjusted_up_probability(0~1), summary(string<=300)。"
        f"\n输入数据:\n{json.dumps(context, ensure_ascii=False)}"
    )
    body = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": settings.gemini_temperature,
            "maxOutputTokens": settings.gemini_max_output_tokens,
            "responseMimeType": "application/json",
        },
    }
    timeout = max(3.0, settings.gemini_timeout_ms / 1000)

    try:
        response = httpx.post(
            url,
            params={"key": settings.gemini_api_key},
            json=body,
            timeout=timeout,
        )
    except Exception as exc:
        raise AiSecondOpinionError(f"gemini request failed: {exc}") from exc

    if response.status_code != 200:
        raise AiSecondOpinionError(f"gemini http {response.status_code}: {response.text[:200]}")

    payload = response.json()
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise AiSecondOpinionError("gemini empty candidates")

    content = candidates[0].get("content", {})
    parts = content.get("parts") if isinstance(content, dict) else None
    if not isinstance(parts, list) or not parts:
        raise AiSecondOpinionError("gemini empty parts")

    raw_text = str(parts[0].get("text", "")).strip()
    if not raw_text:
        raise AiSecondOpinionError("gemini empty text")
    parsed = _parse_json_text(raw_text)
    _validate_gemini_payload(parsed)
    return parsed, raw_text


def _build_context(
    *,
    code: str,
    horizon: str,
    fund_name: str,
    category: str,
    as_of: datetime,
    quote,
    pred,
    news_signal,
    market_ctx,
    factors: list,
    risk_flags: list[str],
    backtest,
) -> dict:
    return {
        "fund": {
            "code": code,
            "name": fund_name,
            "category": category,
            "horizon": horizon,
            "as_of": as_of.isoformat(),
        },
        "quant": {
            "daily_change_pct": quote.daily_change_pct if quote else None,
            "volatility_20d": quote.volatility_20d if quote else None,
            "up_probability": pred.up_probability,
            "expected_return_pct": pred.expected_return_pct,
            "confidence": pred.confidence,
            "top_factors": [{"name": f.name, "contribution": f.contribution} for f in factors],
            "risk_flags": risk_flags,
        },
        "market": {
            "market_score": market_ctx.market_score,
            "style_score": market_ctx.style_score,
            "data_freshness": market_ctx.data_freshness,
            "source_degraded": market_ctx.source_degraded,
        },
        "news": {
            "sentiment_score": news_signal.sentiment_score if news_signal else 0.0,
            "event_score": news_signal.event_score if news_signal else 0.0,
            "volume_shock": news_signal.volume_shock if news_signal else 0.0,
            "sample_title": news_signal.sample_title if news_signal else "暂无新增公告/舆情",
        },
        "reliability": {
            "accuracy": backtest.accuracy if backtest else None,
            "auc": backtest.auc if backtest else None,
            "f1": backtest.f1 if backtest else None,
            "max_drawdown": backtest.max_drawdown if backtest else None,
            "sharpe": backtest.sharpe if backtest else None,
            "sample_size": backtest.sample_size if backtest else None,
        },
    }


def _from_cache_row(row: AiJudgementCache) -> dict:
    try:
        reasons = json.loads(row.key_reasons_json)
    except Exception:
        reasons = []
    try:
        warnings = json.loads(row.risk_warnings_json)
    except Exception:
        warnings = []
    return {
        "code": row.fund_code,
        "horizon": row.horizon,
        "as_of": row.as_of,
        "data_freshness": row.data_freshness,
        "trend": row.trend,
        "trend_strength": row.trend_strength,
        "agreement_with_model": row.agreement_with_model,
        "key_reasons": reasons if isinstance(reasons, list) else [],
        "risk_warnings": warnings if isinstance(warnings, list) else [],
        "confidence_adjustment": row.confidence_adjustment,
        "adjusted_up_probability": row.adjusted_up_probability,
        "summary": row.summary,
        "provider": row.provider,
        "model": row.model,
    }


def peek_ai_second_opinion(db: Session, code: str, horizon: str, as_of: datetime | None = None) -> dict | None:
    AiJudgementCache.__table__.create(bind=db.get_bind(), checkfirst=True)
    cache_model = _cache_model_name()
    stmt = select(AiJudgementCache).where(
        AiJudgementCache.fund_code == code,
        AiJudgementCache.horizon == horizon,
        AiJudgementCache.model == cache_model,
        AiJudgementCache.prompt_version == settings.gemini_prompt_version,
    )
    if as_of is not None:
        stmt = stmt.where(AiJudgementCache.as_of == as_of)
    stmt = stmt.order_by(AiJudgementCache.as_of.desc(), AiJudgementCache.updated_at.desc()).limit(1)
    row = db.scalar(stmt)
    if not row:
        return None
    return _from_cache_row(row)


def get_ai_second_opinion(db: Session, code: str, horizon: str) -> dict:
    # Backward compatibility for existing DBs without schema migrations.
    AiJudgementCache.__table__.create(bind=db.get_bind(), checkfirst=True)

    pred = latest_prediction(db, code, horizon)
    if not pred:
        raise AiSecondOpinionError("prediction not found")

    cache_model = _cache_model_name()
    existing = db.scalar(
        select(AiJudgementCache).where(
            AiJudgementCache.fund_code == code,
            AiJudgementCache.horizon == horizon,
            AiJudgementCache.as_of == pred.as_of,
            AiJudgementCache.model == cache_model,
            AiJudgementCache.prompt_version == settings.gemini_prompt_version,
        )
    )
    if existing:
        return _from_cache_row(existing)

    quote = latest_quote(db, code)
    news_signal = latest_news_signal(db, code)
    market_ctx = get_or_refresh_market_context(db)
    backtest = latest_backtest_report(db, horizon)
    fund_row = db.scalar(select(Fund).where(Fund.code == code))
    fund_name = fund_row.name if fund_row else code
    category = fund_row.category if fund_row else "未知"

    sentiment_score = news_signal.sentiment_score if news_signal else 0.0
    event_score = news_signal.event_score if news_signal else 0.0
    volume_shock = news_signal.volume_shock if news_signal else 0.0
    factors = explain_features(
        horizon=horizon,
        daily_change_pct=quote.daily_change_pct if quote else None,
        volatility_20d=quote.volatility_20d if quote else None,
        sentiment_score=sentiment_score,
        event_score=event_score,
        volume_shock_score=volume_shock,
        market_score=market_ctx.market_score,
        style_score=market_ctx.style_score,
    )
    risk_flags = build_risk_flags(
        volatility_20d=quote.volatility_20d if quote else None,
        confidence=pred.confidence,
        sentiment_score=sentiment_score,
        event_score=event_score,
        volume_shock_score=volume_shock,
        market_source_degraded=market_ctx.source_degraded,
    )

    data_freshness = _freshness(pred.as_of)
    fallback = _fallback_payload(
        code=code,
        horizon=horizon,
        as_of=pred.as_of,
        data_freshness=data_freshness,
        up_probability=float(pred.up_probability),
        expected_return_pct=float(pred.expected_return_pct),
        confidence=float(pred.confidence),
        factors=factors,
        risk_flags=risk_flags,
    )
    if settings.gemini_enabled and settings.gemini_api_key:
        fallback["provider"] = "gemini-fallback"
        fallback["model"] = settings.gemini_model

    payload = fallback
    raw_response: str | None = None
    if settings.gemini_enabled and settings.gemini_api_key:
        context = _build_context(
            code=code,
            horizon=horizon,
            fund_name=fund_name,
            category=category,
            as_of=pred.as_of,
            quote=quote,
            pred=pred,
            news_signal=news_signal,
            market_ctx=market_ctx,
            factors=factors,
            risk_flags=risk_flags,
            backtest=backtest,
        )
        budget_ok = _consume_ai_daily_budget(db)
        if budget_ok:
            try:
                parsed, raw_response = _call_gemini(context)
                payload = _normalize_payload(
                    parsed=parsed,
                    code=code,
                    horizon=horizon,
                    as_of=pred.as_of,
                    data_freshness=data_freshness,
                    up_probability=float(pred.up_probability),
                    expected_return_pct=float(pred.expected_return_pct),
                    factors=factors,
                    risk_flags=risk_flags,
                )
                payload = _apply_compliance_filter(payload)
            except AiSecondOpinionError:
                payload = fallback
        else:
            payload = fallback
            payload["summary"] = "AI调用预算已达当日上限，当前返回规则降级结果（仅供学习研究）。"
            payload["risk_warnings"] = list(
                dict.fromkeys(
                    ["AI预算已用尽，等待次日额度恢复。", *payload.get("risk_warnings", [])]
                )
            )[:6]

    cache_row = AiJudgementCache(
        fund_code=code,
        horizon=horizon,
        as_of=pred.as_of,
        data_freshness=payload["data_freshness"],
        provider=payload["provider"],
        model=payload["model"],
        prompt_version=settings.gemini_prompt_version,
        trend=payload["trend"],
        trend_strength=int(payload["trend_strength"]),
        agreement_with_model=payload["agreement_with_model"],
        key_reasons_json=json.dumps(payload["key_reasons"], ensure_ascii=False),
        risk_warnings_json=json.dumps(payload["risk_warnings"], ensure_ascii=False),
        confidence_adjustment=float(payload["confidence_adjustment"]),
        adjusted_up_probability=float(payload["adjusted_up_probability"]),
        summary=payload["summary"],
        raw_response=raw_response,
    )
    db.add(cache_row)
    db.commit()
    return payload
