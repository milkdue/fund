from app.schemas.fund import ExplainFactor


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _news_impact(
    sentiment_score: float,
    event_score: float,
    volume_shock_score: float,
    horizon: str,
) -> float:
    if horizon == "short":
        return sentiment_score * 1.40 + event_score * 0.90 + volume_shock_score * 0.25
    return sentiment_score * 2.00 + event_score * 1.20 + volume_shock_score * 0.15


def _market_impact(market_score: float, style_score: float, horizon: str) -> float:
    if horizon == "short":
        return market_score * 0.85 + style_score * 0.25
    return market_score * 1.65 + style_score * 0.45


def calibrate_probability(raw_probability: float, horizon: str, market_score: float = 0.0) -> float:
    centered = raw_probability - 0.5
    if horizon == "short":
        calibrated = 0.5 + centered * 0.92 + market_score * 0.012
    else:
        calibrated = 0.5 + centered * 0.88 + market_score * 0.016
    return round(_clamp(calibrated, 0.05, 0.95), 4)


def _compute_prediction_payload(
    *,
    horizon: str,
    base_expected: float,
    volatility_20d: float,
    sentiment_score: float,
    event_score: float,
    volume_shock_score: float,
    market_score: float,
    style_score: float,
    market_degraded: bool,
    expected_scale: float,
) -> dict[str, float]:
    expected_return = (base_expected + _news_impact(sentiment_score, event_score, volume_shock_score, horizon) + _market_impact(market_score, style_score, horizon)) * expected_scale

    raw_probability = _clamp(
        0.5 + expected_return / (20.0 if horizon == "short" else 30.0),
        0.05,
        0.95,
    )
    up_probability = calibrate_probability(raw_probability, horizon, market_score=market_score)

    base_conf = 0.78 if horizon == "short" else 0.72
    vol_div = 18.0 if horizon == "short" else 22.0
    event_bonus = abs(event_score) * (0.05 if horizon == "short" else 0.04)
    shock_penalty = abs(volume_shock_score) * (0.02 if horizon == "short" else 0.01)
    market_penalty = 0.08 if market_degraded else 0.0

    confidence = _clamp(base_conf - volatility_20d / vol_div + event_bonus - shock_penalty - market_penalty, 0.30, 0.88)
    return {
        "up_probability": round(up_probability, 4),
        "expected_return_pct": round(expected_return, 2),
        "confidence": round(confidence, 4),
    }


def rule_based_predictions(
    daily_change_pct: float,
    volatility_20d: float,
    sentiment_score: float = 0.0,
    event_score: float = 0.0,
    volume_shock_score: float = 0.0,
    market_score: float = 0.0,
    style_score: float = 0.0,
    market_degraded: bool = False,
) -> dict[str, dict[str, float]]:
    # Baseline momentum + volatility model, then corrected by news and market factors.
    short_base = daily_change_pct * 1.6 - volatility_20d * 0.1
    mid_base = daily_change_pct * 3.8 - volatility_20d * 0.18

    short_payload = _compute_prediction_payload(
        horizon="short",
        base_expected=short_base,
        volatility_20d=volatility_20d,
        sentiment_score=sentiment_score,
        event_score=event_score,
        volume_shock_score=volume_shock_score,
        market_score=market_score,
        style_score=style_score,
        market_degraded=market_degraded,
        expected_scale=1.0,
    )
    mid_payload = _compute_prediction_payload(
        horizon="mid",
        base_expected=mid_base,
        volatility_20d=volatility_20d,
        sentiment_score=sentiment_score,
        event_score=event_score,
        volume_shock_score=volume_shock_score,
        market_score=market_score,
        style_score=style_score,
        market_degraded=market_degraded,
        expected_scale=1.0,
    )

    return {
        "short": short_payload,
        "mid": mid_payload,
    }


def candidate_rule_predictions(
    daily_change_pct: float,
    volatility_20d: float,
    sentiment_score: float = 0.0,
    event_score: float = 0.0,
    volume_shock_score: float = 0.0,
    market_score: float = 0.0,
    style_score: float = 0.0,
    market_degraded: bool = False,
) -> dict[str, dict[str, float]]:
    # Candidate model: stronger trend + market sensitivity for A/B comparison.
    short_base = daily_change_pct * 1.85 - volatility_20d * 0.12
    mid_base = daily_change_pct * 4.15 - volatility_20d * 0.22
    return {
        "short": _compute_prediction_payload(
            horizon="short",
            base_expected=short_base,
            volatility_20d=volatility_20d,
            sentiment_score=sentiment_score,
            event_score=event_score,
            volume_shock_score=volume_shock_score,
            market_score=market_score * 1.05,
            style_score=style_score * 1.10,
            market_degraded=market_degraded,
            expected_scale=1.04,
        ),
        "mid": _compute_prediction_payload(
            horizon="mid",
            base_expected=mid_base,
            volatility_20d=volatility_20d,
            sentiment_score=sentiment_score,
            event_score=event_score,
            volume_shock_score=volume_shock_score,
            market_score=market_score * 1.12,
            style_score=style_score * 1.08,
            market_degraded=market_degraded,
            expected_scale=1.06,
        ),
    }


def explain_features(
    horizon: str,
    daily_change_pct: float | None = None,
    volatility_20d: float | None = None,
    sentiment_score: float = 0.0,
    event_score: float = 0.0,
    volume_shock_score: float = 0.0,
    market_score: float = 0.0,
    style_score: float = 0.0,
) -> list[ExplainFactor]:
    if daily_change_pct is None or volatility_20d is None:
        # Fallback for incomplete upstream data.
        if horizon == "short":
            return [
                ExplainFactor(name="近5日动量", contribution=0.31),
                ExplainFactor(name="20日波动率", contribution=-0.22),
                ExplainFactor(name="舆情情绪分", contribution=round(sentiment_score * 0.35, 2)),
            ]
        return [
            ExplainFactor(name="估值分位", contribution=0.29),
            ExplainFactor(name="中期趋势", contribution=0.18),
            ExplainFactor(name="舆情延续分", contribution=round(sentiment_score * 0.42, 2)),
        ]

    if horizon == "short":
        factors = [
            ExplainFactor(name="近1日涨跌", contribution=round(_clamp(daily_change_pct / 4.0, -0.6, 0.6), 2)),
            ExplainFactor(name="20日波动率", contribution=round(_clamp(-volatility_20d / 10.0, -0.6, 0.1), 2)),
            ExplainFactor(name="舆情情绪分", contribution=round(_clamp(sentiment_score * 0.45, -0.6, 0.6), 2)),
            ExplainFactor(name="公告事件冲击", contribution=round(_clamp(event_score * 0.50, -0.6, 0.6), 2)),
            ExplainFactor(name="资讯热度冲击", contribution=round(_clamp(volume_shock_score * 0.25, -0.4, 0.5), 2)),
            ExplainFactor(name="市场风险偏好", contribution=round(_clamp(market_score * 0.30, -0.6, 0.6), 2)),
            ExplainFactor(name="成长/价值风格", contribution=round(_clamp(style_score * 0.22, -0.5, 0.5), 2)),
        ]
    else:
        factors = [
            ExplainFactor(name="中期动量", contribution=round(_clamp(daily_change_pct / 2.5, -0.8, 0.8), 2)),
            ExplainFactor(name="波动抑制", contribution=round(_clamp(-volatility_20d / 12.0, -0.7, 0.2), 2)),
            ExplainFactor(name="舆情延续分", contribution=round(_clamp(sentiment_score * 0.55, -0.7, 0.7), 2)),
            ExplainFactor(name="公告事件延续", contribution=round(_clamp(event_score * 0.60, -0.7, 0.7), 2)),
            ExplainFactor(name="资讯热度", contribution=round(_clamp(volume_shock_score * 0.18, -0.4, 0.4), 2)),
            ExplainFactor(name="市场风险偏好", contribution=round(_clamp(market_score * 0.40, -0.8, 0.8), 2)),
            ExplainFactor(name="成长/价值风格", contribution=round(_clamp(style_score * 0.30, -0.7, 0.7), 2)),
        ]

    # Keep the explain card concise by returning top-4 absolute contributors.
    factors.sort(key=lambda x: abs(x.contribution), reverse=True)
    return factors[:4]


def build_risk_flags(
    *,
    volatility_20d: float | None,
    confidence: float,
    sentiment_score: float = 0.0,
    event_score: float = 0.0,
    volume_shock_score: float = 0.0,
    market_source_degraded: bool = False,
) -> list[str]:
    flags: list[str] = []
    if volatility_20d is not None and volatility_20d >= 2.5:
        flags.append("高波动风险")
    if confidence < 0.45:
        flags.append("置信度偏低")
    if sentiment_score <= -0.25:
        flags.append("舆情偏负面")
    if event_score <= -0.25:
        flags.append("公告事件偏利空")
    if abs(volume_shock_score) >= 0.8:
        flags.append("信息热度异常")
    if market_source_degraded:
        flags.append("市场行情因子降级")
    if not flags:
        flags.append("风险整体可控")
    return flags[:4]


def confidence_interval(expected_return_pct: float, confidence: float) -> tuple[float, float]:
    band = max(0.8, (1.0 - confidence) * 6)
    return (round(expected_return_pct - band, 2), round(expected_return_pct + band, 2))
