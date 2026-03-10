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


def rule_based_predictions(
    daily_change_pct: float,
    volatility_20d: float,
    sentiment_score: float = 0.0,
    event_score: float = 0.0,
    volume_shock_score: float = 0.0,
) -> dict[str, dict[str, float]]:
    # Baseline momentum + volatility model, then corrected by news sentiment/event factors.
    short_base = daily_change_pct * 1.6 - volatility_20d * 0.1
    mid_base = daily_change_pct * 3.8 - volatility_20d * 0.18

    short_expected = short_base + _news_impact(sentiment_score, event_score, volume_shock_score, "short")
    mid_expected = mid_base + _news_impact(sentiment_score, event_score, volume_shock_score, "mid")

    short_prob = _clamp(0.5 + short_expected / 20.0, 0.05, 0.95)
    mid_prob = _clamp(0.5 + mid_expected / 30.0, 0.05, 0.95)

    short_conf = _clamp(
        0.78 - volatility_20d / 18.0 + abs(event_score) * 0.05 - abs(volume_shock_score) * 0.02,
        0.35,
        0.88,
    )
    mid_conf = _clamp(
        0.72 - volatility_20d / 22.0 + abs(event_score) * 0.04 - abs(volume_shock_score) * 0.01,
        0.30,
        0.84,
    )

    return {
        "short": {
            "up_probability": round(short_prob, 4),
            "expected_return_pct": round(short_expected, 2),
            "confidence": round(short_conf, 4),
        },
        "mid": {
            "up_probability": round(mid_prob, 4),
            "expected_return_pct": round(mid_expected, 2),
            "confidence": round(mid_conf, 4),
        },
    }


def explain_features(
    horizon: str,
    daily_change_pct: float | None = None,
    volatility_20d: float | None = None,
    sentiment_score: float = 0.0,
    event_score: float = 0.0,
    volume_shock_score: float = 0.0,
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
        ]
    else:
        factors = [
            ExplainFactor(name="中期动量", contribution=round(_clamp(daily_change_pct / 2.5, -0.8, 0.8), 2)),
            ExplainFactor(name="波动抑制", contribution=round(_clamp(-volatility_20d / 12.0, -0.7, 0.2), 2)),
            ExplainFactor(name="舆情延续分", contribution=round(_clamp(sentiment_score * 0.55, -0.7, 0.7), 2)),
            ExplainFactor(name="公告事件延续", contribution=round(_clamp(event_score * 0.60, -0.7, 0.7), 2)),
            ExplainFactor(name="资讯热度", contribution=round(_clamp(volume_shock_score * 0.18, -0.4, 0.4), 2)),
        ]

    # Keep the explain card concise by returning top-4 absolute contributors.
    factors.sort(key=lambda x: abs(x.contribution), reverse=True)
    return factors[:4]


def confidence_interval(expected_return_pct: float, confidence: float) -> tuple[float, float]:
    band = max(0.8, (1.0 - confidence) * 6)
    return (round(expected_return_pct - band, 2), round(expected_return_pct + band, 2))
