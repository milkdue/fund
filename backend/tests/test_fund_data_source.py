from app.services.fund_data_source import _calc_daily_change, _calc_volatility_20d, _load_json_value, _load_string_value


SAMPLE_SCRIPT = '''
var fS_name = "样例基金";
var Data_netWorthTrend = [{"x":1704067200000,"y":1.0},{"x":1704153600000,"y":1.02},{"x":1704240000000,"y":1.01}];
'''


def test_load_values_from_script():
    assert _load_string_value(SAMPLE_SCRIPT, "fS_name") == "样例基金"
    trend = _load_json_value(SAMPLE_SCRIPT, "Data_netWorthTrend")
    assert len(trend) == 3


def test_metrics_calculation():
    net_values = [1.0, 1.02, 1.01, 1.03, 1.04]
    assert _calc_daily_change(net_values) == 0.97
    assert _calc_volatility_20d(net_values) >= 0
