from datetime import datetime, timedelta

from app.services.quote_quality_service import evaluate_intraday_estimate_quality, evaluate_official_nav_quality


def test_official_quote_quality_flags_large_jump():
    result = evaluate_official_nav_quality(
        as_of=datetime.now() - timedelta(hours=2),
        nav=2.0,
        daily_change_pct=1.2,
        volatility_20d=1.1,
        source="eastmoney_pingzhongdata",
        previous_nav=1.5,
        previous_as_of=datetime.now() - timedelta(days=1),
    )
    assert result.status == "error"
    assert "与上一净值跳变异常" in result.flags


def test_intraday_quality_warns_on_stale_and_deviation():
    result = evaluate_intraday_estimate_quality(
        as_of=datetime.now() - timedelta(hours=4),
        estimate_nav=2.3,
        estimate_change_pct=1.5,
        source="eastmoney_fundgz",
        reference_nav=2.0,
    )
    assert result.status == "warn"
    assert "盘中估值已过期" in result.flags
    assert "与最近正式净值偏离较大" in result.flags
