from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.services.time_utils import shanghai_now_naive


SOURCE_LABELS = {
    "eastmoney_pingzhongdata": "东方财富正式净值",
    "akshare_fund_open_fund_info_em": "AKShare 净值回退源",
    "eastmoney_fundgz": "东方财富盘中估值",
}


@dataclass
class QuoteQualityResult:
    status: str
    flags: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    source_label: str = "未知来源"


def source_label(source: str | None) -> str:
    return SOURCE_LABELS.get(source or "", source or "未知来源")


def _status_from_flags(errors: list[str], warnings: list[str]) -> str:
    if errors:
        return "error"
    if warnings:
        return "warn"
    return "ok"


def evaluate_official_nav_quality(
    *,
    as_of: datetime,
    nav: float,
    daily_change_pct: float,
    volatility_20d: float,
    source: str | None,
    previous_nav: float | None = None,
    previous_as_of: datetime | None = None,
) -> QuoteQualityResult:
    errors: list[str] = []
    warnings: list[str] = []
    notes: list[str] = []
    now = shanghai_now_naive()

    if nav <= 0:
        errors.append("净值无效")
    if as_of > now.replace(hour=23, minute=59, second=59, microsecond=0):
        errors.append("时间异常")
    if abs(daily_change_pct) > 15:
        errors.append("单日涨跌异常")
    elif abs(daily_change_pct) > 8:
        warnings.append("单日波动偏大")

    if volatility_20d < 0 or volatility_20d > 12:
        errors.append("20日波动异常")
    elif volatility_20d > 4:
        warnings.append("20日波动偏高")

    age_hours = (now - as_of).total_seconds() / 3600
    if age_hours > 72:
        warnings.append("净值已明显滞后")
    elif age_hours > 36:
        warnings.append("净值略有延迟")

    if previous_nav and previous_nav > 0 and previous_as_of and previous_as_of < as_of:
        realized_change = round((nav - previous_nav) / previous_nav * 100, 2)
        delta_gap = abs(realized_change - daily_change_pct)
        if abs(realized_change) > 20:
            errors.append("与上一净值跳变异常")
            notes.append("相邻净值跳变超过 20%，更像是分红拆分或异常数据。")
        elif delta_gap > 3:
            warnings.append("与上一净值变化不一致")
            notes.append("展示涨跌幅与相邻净值推导结果偏差较大。")

    return QuoteQualityResult(
        status=_status_from_flags(errors, warnings),
        flags=errors + warnings,
        notes=notes,
        source_label=source_label(source),
    )


def evaluate_intraday_estimate_quality(
    *,
    as_of: datetime,
    estimate_nav: float,
    estimate_change_pct: float,
    source: str | None,
    reference_nav: float | None = None,
) -> QuoteQualityResult:
    errors: list[str] = []
    warnings: list[str] = []
    now = shanghai_now_naive()

    if estimate_nav <= 0:
        errors.append("估值无效")
    if abs(estimate_change_pct) > 15:
        errors.append("盘中估值涨跌异常")
    elif abs(estimate_change_pct) > 8:
        warnings.append("盘中估值波动偏大")

    age_minutes = (now - as_of).total_seconds() / 60
    if age_minutes > 180:
        warnings.append("盘中估值已过期")
    elif age_minutes > 45:
        warnings.append("盘中估值更新较慢")

    if reference_nav and reference_nav > 0:
        deviation = abs((estimate_nav - reference_nav) / reference_nav * 100)
        if deviation > 8:
            warnings.append("与最近正式净值偏离较大")

    return QuoteQualityResult(
        status=_status_from_flags(errors, warnings),
        flags=errors + warnings,
        notes=[],
        source_label=source_label(source),
    )
