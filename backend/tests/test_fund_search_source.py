from app.services.fund_search_source import _extract_list


SAMPLE = 'var r = [["110022","yfdxfhy","易方达消费行业混合","混合型"],["161725","zszzbjzs","招商中证白酒指数","指数型"]];'


def test_extract_list():
    rows = _extract_list(SAMPLE)
    assert len(rows) == 2
    assert rows[0][0] == "110022"
    assert rows[0][2] == "易方达消费行业混合"
