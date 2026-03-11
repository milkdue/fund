from app.services.fund_search_source import _extract_list, _is_supported_result


SAMPLE = 'var r = [["110022","yfdxfhy","易方达消费行业混合","混合型"],["161725","zszzbjzs","招商中证白酒指数","指数型"]];'


def test_extract_list():
    rows = _extract_list(SAMPLE)
    assert len(rows) == 2
    assert rows[0][0] == "110022"
    assert rows[0][2] == "易方达消费行业混合"


def test_backend_share_class_is_excluded():
    assert _is_supported_result("嘉实沪深300指数研究增强A") is True
    assert _is_supported_result("富国沪深300指数增强A(后端)") is False
    assert _is_supported_result("富国上证指数ETF联接A（后端）") is False
