from __future__ import annotations

from collections.abc import Iterable


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


POSITIVE_KEYWORDS: dict[str, float] = {
    "增长": 0.35,
    "提升": 0.25,
    "回升": 0.25,
    "超预期": 0.45,
    "创新高": 0.40,
    "增持": 0.35,
    "分红": 0.20,
    "获批": 0.28,
    "利好": 0.40,
}

NEGATIVE_KEYWORDS: dict[str, float] = {
    "下滑": -0.30,
    "下降": -0.28,
    "亏损": -0.45,
    "减持": -0.35,
    "回撤": -0.26,
    "风险": -0.22,
    "利空": -0.40,
    "终止": -0.30,
    "违约": -0.45,
}

POSITIVE_EVENTS: dict[str, float] = {
    "基金经理增聘": 0.24,
    "分红公告": 0.20,
    "持仓调整": 0.10,
    "规模增长": 0.20,
    "开放申购": 0.10,
}

NEGATIVE_EVENTS: dict[str, float] = {
    "基金经理离任": -0.35,
    "暂停申购": -0.22,
    "大额赎回": -0.26,
    "清盘": -0.50,
    "异常波动": -0.18,
}


def score_headline(title: str) -> tuple[float, float]:
    text = title.strip()
    if not text:
        return 0.0, 0.0

    sentiment_raw = 0.0
    for keyword, weight in POSITIVE_KEYWORDS.items():
        if keyword in text:
            sentiment_raw += weight
    for keyword, weight in NEGATIVE_KEYWORDS.items():
        if keyword in text:
            sentiment_raw += weight

    event_raw = 0.0
    for keyword, weight in POSITIVE_EVENTS.items():
        if keyword in text:
            event_raw += weight
    for keyword, weight in NEGATIVE_EVENTS.items():
        if keyword in text:
            event_raw += weight

    return round(_clamp(sentiment_raw, -1.0, 1.0), 4), round(_clamp(event_raw, -1.0, 1.0), 4)


def aggregate_scores(rows: Iterable[tuple[float, float]]) -> tuple[float, float]:
    sentiment_total = 0.0
    event_total = 0.0
    count = 0
    for sentiment, event in rows:
        sentiment_total += sentiment
        event_total += event
        count += 1

    if count == 0:
        return 0.0, 0.0
    return round(sentiment_total / count, 4), round(event_total / count, 4)


def volume_shock(current_count: int, history_counts: list[int]) -> float:
    baseline = 0.0
    if history_counts:
        baseline = sum(history_counts) / len(history_counts)
    if baseline <= 0:
        return 0.0
    shock = (current_count - baseline) / baseline
    return round(_clamp(shock, -1.0, 2.0), 4)
