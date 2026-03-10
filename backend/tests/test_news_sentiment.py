from app.services.news_sentiment import aggregate_scores, score_headline, volume_shock
from app.services.predictor import explain_features, rule_based_predictions


def test_score_headline_detects_positive_and_event():
    sentiment, event = score_headline("基金经理增聘并宣布分红，规模增长超预期")
    assert sentiment > 0
    assert event > 0


def test_score_headline_detects_negative_and_event():
    sentiment, event = score_headline("基金经理离任并暂停申购，净值下滑存在风险")
    assert sentiment < 0
    assert event < 0


def test_aggregate_and_volume_shock():
    sentiment, event = aggregate_scores([(0.4, 0.1), (-0.2, -0.1), (0.2, 0.0)])
    assert sentiment == 0.1333
    assert event == 0.0
    assert volume_shock(current_count=20, history_counts=[10, 12, 8]) > 0


def test_news_factor_changes_prediction_and_explain():
    base = rule_based_predictions(0.6, 1.5)
    pos = rule_based_predictions(0.6, 1.5, sentiment_score=0.6, event_score=0.3, volume_shock_score=0.5)
    neg = rule_based_predictions(0.6, 1.5, sentiment_score=-0.6, event_score=-0.3, volume_shock_score=0.5)

    assert pos["short"]["expected_return_pct"] > base["short"]["expected_return_pct"]
    assert neg["short"]["expected_return_pct"] < base["short"]["expected_return_pct"]

    factors = explain_features(
        horizon="short",
        daily_change_pct=0.6,
        volatility_20d=1.5,
        sentiment_score=0.5,
        event_score=0.4,
        volume_shock_score=0.3,
    )
    names = [f.name for f in factors]
    assert "舆情情绪分" in names
    assert "公告事件冲击" in names
