from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


@dataclass
class ScoreComponentResult:
    key: str
    label: str
    score: int
    summary: str
    detail_lines: list[str]


@dataclass
class ScoreCardResult:
    horizon: str
    total_score: int
    risk_score: int
    action_label: str
    signal_bias: str
    summary: str
    components: list[ScoreComponentResult]


def _horizon_window_text(horizon: str) -> str:
    return "未来1-7天" if horizon == "short" else "未来1-3个月"


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


def _agreement_text(value: str | None) -> str:
    lowered = (value or "").lower()
    if lowered == "agree":
        return "AI 与量化同向"
    if lowered == "partial":
        return "AI 与量化部分一致"
    if lowered == "disagree":
        return "AI 与量化存在分歧"
    return "暂无 AI 一致性判断"


def _signal_bias_summary(
    *,
    signal_bias: str,
    horizon: str,
    up_probability: float,
    expected_return_pct: float,
) -> str:
    window = _horizon_window_text(horizon)
    if signal_bias == "偏多":
        strength = "上行倾向较明确" if up_probability >= 0.66 or expected_return_pct >= (2.6 if horizon == "short" else 6.0) else "略偏上行"
        return f"{window}{strength}"
    if signal_bias == "偏空":
        strength = "回落压力较明显" if up_probability <= 0.40 or expected_return_pct <= (-1.2 if horizon == "short" else -3.5) else "略偏下行"
        return f"{window}{strength}"
    if up_probability >= 0.55 and expected_return_pct >= 0:
        return f"{window}震荡中略偏上行"
    if up_probability <= 0.45 or expected_return_pct < 0:
        return f"{window}震荡中略偏下行"
    return f"{window}更可能区间震荡"


def _market_state_text(market_score: float) -> str:
    if market_score >= 1.1:
        return "市场明显偏暖"
    if market_score >= 0.35:
        return "市场中性偏暖"
    if market_score > -0.35:
        return "市场中性震荡"
    if market_score > -1.1:
        return "市场偏弱"
    return "市场承压明显"


def _style_state_text(style_score: float) -> str:
    if style_score >= 1.0:
        return "成长风格明显占优"
    if style_score >= 0.25:
        return "成长风格略占优"
    if style_score <= -1.0:
        return "价值/大盘风格明显占优"
    if style_score <= -0.25:
        return "价值/大盘风格略占优"
    return "风格相对均衡"


def _market_implication_text(market_score: float, style_score: float) -> str:
    if market_score >= 0.35:
        if style_score >= 0.25:
            return "风险偏好有改善，强势成长方向更容易获得溢价，但不宜追高。"
        if style_score <= -0.25:
            return "风险偏好有改善，但资金更偏向大盘/价值方向。"
        return "市场情绪不差，顺势观察强势方向比逆势抄底更合适。"
    if market_score <= -0.35:
        return "市场整体偏谨慎，更适合控制仓位，减少激进操作。"
    return "市场缺少明确趋势，适合以观察和分批决策为主。"


def _narrative_state_text(
    *,
    sentiment_score: float,
    event_score: float,
    volume_shock_score: float,
    headline_count: int,
) -> str:
    if headline_count <= 0:
        return "近3日未抓到显著公告/舆情，按中性处理"

    composite = 0.55 * sentiment_score + 0.35 * event_score + 0.10 * volume_shock_score
    if composite >= 0.25:
        return "近3日公告/舆情偏利好"
    if composite <= -0.25:
        return "近3日公告/舆情偏利空"
    return "近3日公告/舆情偏中性"


def _volume_shock_text(volume_shock_score: float) -> str:
    if volume_shock_score >= 0.5:
        return "热度明显升温"
    if volume_shock_score >= 0.15:
        return "热度略有升温"
    if volume_shock_score <= -0.5:
        return "热度明显降温"
    if volume_shock_score <= -0.15:
        return "热度略有降温"
    return "热度基本平稳"


def _clean_sample_title(title: str | None) -> str | None:
    cleaned = (title or "").strip()
    if not cleaned or cleaned == "暂无新增公告/舆情":
        return None
    return cleaned[:80]


def _freshness_text(value: str) -> str:
    lowered = (value or "").lower()
    if lowered == "fresh":
        return "新鲜"
    if lowered == "lagging":
        return "一般"
    if lowered == "stale":
        return "过期"
    return "未知"


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
    news_headline_count: int = 0,
    news_sample_title: str | None = None,
    risk_flags: list[str] | None = None,
    market_source_degraded: bool = False,
    ai_payload: Mapping[str, object] | None = None,
) -> ScoreCardResult:
    risk_flags = risk_flags or []
    agreement = str(ai_payload.get("agreement_with_model", "")) if ai_payload else None
    ai_prob = float(ai_payload.get("adjusted_up_probability", up_probability)) if ai_payload else up_probability
    agreement_text = _agreement_text(agreement)

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
    direction_view = _signal_bias_summary(
        signal_bias=signal_bias,
        horizon=horizon,
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

    market_phrase = _market_state_text(market_score)
    style_phrase = _style_state_text(style_score)
    narrative_phrase = _narrative_state_text(
        sentiment_score=sentiment_score,
        event_score=event_score,
        volume_shock_score=volume_shock_score,
        headline_count=news_headline_count,
    )
    risk_phrase = "风险相对可控" if risk_score >= 65 else "风险中等" if risk_score >= 45 else "风险偏高"
    ai_phrase = ""
    if ai_payload:
        ai_phrase = {
            "agree": "，AI 与量化同向",
            "partial": "，AI 与量化部分一致",
            "disagree": "，AI 与量化存在分歧",
        }.get((agreement or "").lower(), "")
    summary = (
        f"{action_label}，综合评分{total_score}。方向结论：{direction_view}。"
        f"上涨概率 {up_probability * 100:.2f}%，预期涨跌幅 {expected_return_pct:.2f}%。"
        f"市场结论：{market_phrase}，{style_phrase}。"
        f"舆情结论：{narrative_phrase}。{risk_phrase}{ai_phrase}。"
    )

    direction_summary = (
        f"方向结论：{direction_view}。因为上涨概率 {up_probability * 100:.2f}%"
        + (f"、AI 调整后概率 {ai_prob * 100:.2f}%" if ai_payload else "")
        + f"、{agreement_text if ai_payload else '当前未接入 AI 加权'}，所以方向判断 {int(_clamp(direction_score, 0.0, 100.0))} 分。"
    )
    direction_details = [
        f"方向结论：{direction_view}",
        f"量化上涨概率：{up_probability * 100:.2f}%",
        *( [f"AI 调整后上涨概率：{ai_prob * 100:.2f}%"] if ai_payload else [] ),
        f"一致性判断：{agreement_text}",
    ]

    upside_summary = (
        f"因为预期涨跌幅 {expected_return_pct:.2f}% 且置信度 {confidence * 100:.2f}%，"
        f"所以空间收益 {int(_clamp(upside_score, 0.0, 100.0))} 分。"
    )
    upside_details = [
        f"预期涨跌幅：{expected_return_pct:.2f}%",
        f"量化置信度：{confidence * 100:.2f}%",
        f"评分区间基准：{expected_lower:.1f}% ~ {expected_upper:.1f}%",
    ]

    market_summary = (
        f"市场结论：{market_phrase}，{style_phrase}。因为市场环境分 {market_score:.2f}、风格偏好分 {style_score:.2f}，"
        f"所以市场环境 {int(_clamp(market_component, 0.0, 100.0))} 分。"
    )
    market_details = [
        f"市场结论：{market_phrase}",
        f"风格结论：{style_phrase}",
        f"当前含义：{_market_implication_text(market_score, style_score)}",
        f"市场环境分：{market_score:.2f}",
        f"风格偏好分：{style_score:.2f}",
        f"市场源状态：{'降级' if market_source_degraded else '正常'}",
    ]

    sample_title = _clean_sample_title(news_sample_title)
    narrative_summary = (
        f"舆情结论：{narrative_phrase}。因为舆情情绪 {sentiment_score:.2f}、公告事件 {event_score:.2f}、热度冲击 {volume_shock_score:.2f}，"
        f"所以舆情事件 {int(_clamp(narrative_score, 0.0, 100.0))} 分。"
    )
    narrative_details = [
        f"舆情结论：{narrative_phrase}",
        f"近3日抓取样本：{news_headline_count} 条",
        *( [f"代表性标题：{sample_title}"] if sample_title else ["代表性标题：暂无可用公告/舆情样本"] ),
        f"热度判断：{_volume_shock_text(volume_shock_score)}",
        f"舆情情绪分：{sentiment_score:.2f}",
        f"事件冲击分：{event_score:.2f}",
        f"热度冲击分：{volume_shock_score:.2f}",
    ]

    risk_summary = (
        f"因为20日波动率 {volatility_20d:.2f}%"
        if volatility_20d is not None
        else "因为当前缺少波动率数据"
    ) + (
        f"，风险标签 {len(risk_flags)} 个，所以风险控制 {int(_clamp(risk_control_score, 0.0, 100.0))} 分。"
    )
    risk_details = [
        f"风险结论：{'当前波动不大，风险可控' if risk_score >= 65 else '风险处于中等区间' if risk_score >= 45 else '波动和不确定性偏高'}",
        f"20日波动率：{f'{volatility_20d:.2f}%' if volatility_20d is not None else '暂无'}",
        f"风险标签数量：{_risk_flag_count(risk_flags)}",
        f"风险标签：{'、'.join(risk_flags[:3]) if risk_flags else '暂无'}",
    ]

    credibility_summary = (
        f"可信度结论：当前数据{_freshness_text(data_freshness)}。因为量化置信度 {confidence * 100:.2f}% 、数据新鲜度 {_freshness_text(data_freshness)}，"
        f"所以可信度 {int(_clamp(credibility_score, 0.0, 100.0))} 分。"
    )
    credibility_details = [
        f"可信度结论：{'当前可参考性较好' if credibility_score >= 70 else '当前可参考性一般' if credibility_score >= 45 else '当前可参考性偏弱'}",
        f"量化置信度：{confidence * 100:.2f}%",
        f"数据新鲜度：{_freshness_text(data_freshness)}",
        f"市场数据源：{'降级' if market_source_degraded else '正常'}",
    ]

    components = [
        ScoreComponentResult("direction", "方向判断", int(_clamp(direction_score, 0.0, 100.0)), direction_summary, direction_details),
        ScoreComponentResult("upside", "空间收益", int(_clamp(upside_score, 0.0, 100.0)), upside_summary, upside_details),
        ScoreComponentResult("market", "市场环境", int(_clamp(market_component, 0.0, 100.0)), market_summary, market_details),
        ScoreComponentResult("narrative", "舆情事件", int(_clamp(narrative_score, 0.0, 100.0)), narrative_summary, narrative_details),
        ScoreComponentResult("risk_control", "风险控制", int(_clamp(risk_control_score, 0.0, 100.0)), risk_summary, risk_details),
        ScoreComponentResult("credibility", "可信度", int(_clamp(credibility_score, 0.0, 100.0)), credibility_summary, credibility_details),
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
