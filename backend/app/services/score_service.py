from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass
class ScoreComponentResult:
    key: str
    label: str
    score: int
    summary: str


@dataclass
class ScoreCardResult:
    horizon: str
    total_score: int
    risk_score: int
    action_label: str
    signal_bias: str
    summary: str
    components: list[ScoreComponentResult]


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _scale(value: float, lower: float, upper: float) -> float:
    if upper <= lower:
        return 50.0
    return _clamp((value - lower) / (upper - lower) * 100.0, 0.0, 100.0)


def _freshness_score(value: str) -> float:
    lowered = (value or "").lower()
    if lowered == "fresh":
        return 92.0
    if lowered == "lagging":
        return 68.0
    if lowered == "stale":
        return 34.0
    return 55.0


def _agreement_score(value: str | None) -> float:
    lowered = (value or "").lower()
    if lowered == "agree":
        return 84.0
    if lowered == "partial":
        return 62.0
    if lowered == "disagree":
        return 30.0
    return 58.0


def _risk_flag_count(risk_flags: list[str]) -> int:
    return len([flag for flag in risk_flags if flag and flag != "风险整体可控"])


def risk_level_from_score(risk_score: int) -> str:
    if risk_score >= 70:
        return "low"
    if risk_score >= 45:
        return "medium"
    return "high"


def _signal_bias(*, total_score: int, up_probability: float, expected_return_pct: float) -> str:
    if total_score >= 72 and up_probability >= 0.58 and expected_return_pct >= 0:
        return "偏多"
    if total_score <= 52 or up_probability <= 0.45 or expected_return_pct < 0:
        return "偏空"
    return "震荡"


def _action_label(
    *,
    total_score: int,
    risk_score: int,
    data_freshness: str,
    agreement: str | None,
    market_source_degraded: bool,
    expected_return_pct: float,
) -> str:
    if total_score >= 80:
        label = "强关注"
    elif total_score >= 70:
        label = "关注"
    elif total_score >= 60:
        label = "观察"
    else:
        label = "回避"

    if risk_score < 35 or expected_return_pct <= -0.6:
        return "回避"
    if risk_score < 45 and label in {"强关注", "关注"}:
        label = "观察"
    if data_freshness == "stale" and label in {"强关注", "关注"}:
        label = "观察"
    if (agreement or "").lower() == "disagree" and label in {"强关注", "关注"}:
        label = "观察"
    if market_source_degraded and label == "强关注":
        label = "关注"
    return label


def build_prediction_scorecard(
    *,
    horizon: str,
    up_probability: float,
    expected_return_pct: float,
    confidence: float,
    data_freshness: str,
    volatility_20d: float | None,
    market_score: float = 0.0,
    style_score: float = 0.0,
    sentiment_score: float = 0.0,
    event_score: float = 0.0,
    volume_shock_score: float = 0.0,
    risk_flags: list[str] | None = None,
    market_source_degraded: bool = False,
    ai_payload: Mapping[str, object] | None = None,
) -> ScoreCardResult:
    risk_flags = risk_flags or []
    agreement = str(ai_payload.get("agreement_with_model", "")) if ai_payload else None
    ai_prob = float(ai_payload.get("adjusted_up_probability", up_probability)) if ai_payload else up_probability

    quant_prob_score = _clamp(up_probability * 100.0, 0.0, 100.0)
    ai_prob_score = _clamp(ai_prob * 100.0, 0.0, 100.0)
    alignment_score = _agreement_score(agreement)
    direction_score = round(
        (
            0.60 * quant_prob_score
            + (0.25 * ai_prob_score if ai_payload else 0.15 * quant_prob_score)
            + (0.15 * alignment_score if ai_payload else 0.25 * 58.0)
        )
    )

    expected_lower, expected_upper = (-2.5, 4.0) if horizon == "short" else (-6.0, 12.0)
    upside_score = round(
        0.75 * _scale(expected_return_pct, expected_lower, expected_upper)
        + 0.25 * _clamp(confidence * 100.0, 0.0, 100.0)
    )

    market_weight = 0.70 if horizon == "short" else 0.60
    style_weight = 0.30 if horizon == "short" else 0.40
    market_component = round(
        market_weight * _scale(market_score, -2.5, 2.5)
        + style_weight * _scale(style_score, -3.0, 3.0)
    )

    narrative_score = round(
        0.50 * _scale(sentiment_score, -1.0, 1.0)
        + 0.30 * _scale(event_score, -1.0, 1.0)
        + 0.20 * _scale(volume_shock_score, -1.2, 1.2)
    )

    vol_score = 58.0 if volatility_20d is None else 100.0 - _scale(volatility_20d, 0.8, 3.2)
    flag_score = max(15.0, 100.0 - _risk_flag_count(risk_flags) * 18.0)
    risk_control_score = round(0.65 * vol_score + 0.35 * flag_score)

    credibility_score = round(
        0.70 * _clamp(confidence * 100.0, 0.0, 100.0)
        + 0.30 * _freshness_score(data_freshness)
        - (12.0 if market_source_degraded else 0.0)
    )
    credibility_score = int(_clamp(credibility_score, 0.0, 100.0))

    if horizon == "short":
        total_score = round(
            0.30 * direction_score
            + 0.15 * upside_score
            + 0.15 * market_component
            + 0.15 * narrative_score
            + 0.15 * risk_control_score
            + 0.10 * credibility_score
        )
    else:
        total_score = round(
            0.22 * direction_score
            + 0.18 * upside_score
            + 0.20 * market_component
            + 0.10 * narrative_score
            + 0.15 * risk_control_score
            + 0.15 * credibility_score
        )

    risk_score = round(
        0.45 * vol_score
        + 0.30 * _clamp(confidence * 100.0, 0.0, 100.0)
        + 0.15 * _freshness_score(data_freshness)
        + 0.10 * flag_score
        - (12.0 if (agreement or "").lower() == "disagree" else 0.0)
        - (10.0 if market_source_degraded else 0.0)
    )
    risk_score = int(_clamp(risk_score, 0.0, 100.0))
    total_score = int(_clamp(total_score, 0.0, 100.0))

    signal_bias = _signal_bias(
        total_score=total_score,
        up_probability=up_probability,
        expected_return_pct=expected_return_pct,
    )
    action_label = _action_label(
        total_score=total_score,
        risk_score=risk_score,
        data_freshness=data_freshness,
        agreement=agreement,
        market_source_degraded=market_source_degraded,
        expected_return_pct=expected_return_pct,
    )

    market_phrase = "市场环境偏正面" if market_component >= 65 else "市场环境一般" if market_component >= 45 else "市场环境偏弱"
    risk_phrase = "风险相对可控" if risk_score >= 65 else "风险中等" if risk_score >= 45 else "风险偏高"
    ai_phrase = ""
    if ai_payload:
        ai_phrase = {
            "agree": "，AI 与量化同向",
            "partial": "，AI 与量化部分一致",
            "disagree": "，AI 与量化存在分歧",
        }.get((agreement or "").lower(), "")
    summary = f"{action_label}，综合评分{total_score}。{market_phrase}，{risk_phrase}{ai_phrase}。"

    components = [
        ScoreComponentResult("direction", "方向判断", int(_clamp(direction_score, 0.0, 100.0)), "结合上涨概率与 AI 第二意见后的方向分。"),
        ScoreComponentResult("upside", "空间收益", int(_clamp(upside_score, 0.0, 100.0)), "综合预期涨跌幅与置信度后的空间分。"),
        ScoreComponentResult("market", "市场环境", int(_clamp(market_component, 0.0, 100.0)), "由市场环境分和风格偏好分共同构成。"),
        ScoreComponentResult("narrative", "舆情事件", int(_clamp(narrative_score, 0.0, 100.0)), "由舆情、公告事件和热度冲击共同构成。"),
        ScoreComponentResult("risk_control", "风险控制", int(_clamp(risk_control_score, 0.0, 100.0)), "波动越低、负面风险标签越少，得分越高。"),
        ScoreComponentResult("credibility", "可信度", int(_clamp(credibility_score, 0.0, 100.0)), "由预测置信度、数据新鲜度和数据源健康共同决定。"),
    ]
    return ScoreCardResult(
        horizon=horizon,
        total_score=total_score,
        risk_score=risk_score,
        action_label=action_label,
        signal_bias=signal_bias,
        summary=summary,
        components=components,
    )
