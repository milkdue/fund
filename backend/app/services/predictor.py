from app.schemas.fund import ExplainFactor


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def rule_based_predictions(daily_change_pct: float, volatility_20d: float) -> dict[str, dict[str, float]]:
    # MVP baseline: short horizon leans on recent momentum, mid horizon smooths volatility noise.
    short_expected = daily_change_pct * 1.6 - volatility_20d * 0.1
    mid_expected = daily_change_pct * 3.8 - volatility_20d * 0.18

    short_prob = _clamp(0.5 + short_expected / 20.0, 0.05, 0.95)
    mid_prob = _clamp(0.5 + mid_expected / 30.0, 0.05, 0.95)

    short_conf = _clamp(0.78 - volatility_20d / 18.0, 0.35, 0.85)
    mid_conf = _clamp(0.72 - volatility_20d / 22.0, 0.30, 0.82)

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


def explain_features(horizon: str) -> list[ExplainFactor]:
    if horizon == "short":
        return [
            ExplainFactor(name="近5日动量", contribution=0.31),
            ExplainFactor(name="20日波动率", contribution=-0.22),
            ExplainFactor(name="行业强弱", contribution=0.16),
        ]
    return [
        ExplainFactor(name="估值分位", contribution=0.29),
        ExplainFactor(name="盈利预期修正", contribution=0.23),
        ExplainFactor(name="中期趋势", contribution=0.18),
    ]


def confidence_interval(expected_return_pct: float, confidence: float) -> tuple[float, float]:
    band = max(0.8, (1.0 - confidence) * 6)
    return (round(expected_return_pct - band, 2), round(expected_return_pct + band, 2))
