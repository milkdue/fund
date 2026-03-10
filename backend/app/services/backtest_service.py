from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from math import sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import ModelBacktestReport, Prediction, Quote


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _auc_score(y_true: list[int], y_prob: list[float]) -> float:
    positives = [p for p, y in zip(y_prob, y_true) if y == 1]
    negatives = [p for p, y in zip(y_prob, y_true) if y == 0]
    if not positives or not negatives:
        return 0.5

    wins = 0.0
    total = 0
    for p in positives:
        for n in negatives:
            total += 1
            if p > n:
                wins += 1.0
            elif p == n:
                wins += 0.5
    return round(_clamp(wins / total if total else 0.5, 0.0, 1.0), 4)


def _classification_metrics(y_true: list[int], y_pred: list[int]) -> tuple[float, float, float, float]:
    if not y_true:
        return 0.0, 0.0, 0.0, 0.0

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    accuracy = (tp + tn) / len(y_true)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return round(accuracy, 4), round(precision, 4), round(recall, 4), round(f1, 4)


def _strategy_metrics(returns: list[float]) -> tuple[float, float, float]:
    if not returns:
        return 0.0, 0.0, 0.0

    mean_daily = sum(returns) / len(returns)
    variance = sum((r - mean_daily) ** 2 for r in returns) / len(returns)
    std_daily = sqrt(variance)

    annualized = mean_daily * 252
    sharpe = (mean_daily / std_daily * sqrt(252)) if std_daily > 0 else 0.0

    cumulative = 1.0
    peak = 1.0
    max_drawdown = 0.0
    for r in returns:
        cumulative *= 1.0 + r
        if cumulative > peak:
            peak = cumulative
        drawdown = (cumulative - peak) / peak
        if drawdown < max_drawdown:
            max_drawdown = drawdown

    return round(annualized, 4), round(max_drawdown, 4), round(sharpe, 4)


def _model_version_by_horizon(horizon: str) -> str:
    return settings.model_short_version if horizon == "short" else settings.model_mid_version


def generate_backtest_report(
    db: Session,
    horizon: str,
    window_days: int = 180,
    report_date: date | None = None,
) -> ModelBacktestReport:
    target_date = report_date or datetime.now(tz=UTC).date()
    start_at = datetime.combine(target_date - timedelta(days=window_days), time.min)
    end_at = datetime.combine(target_date + timedelta(days=1), time.min)

    rows = list(
        db.execute(
            select(Prediction, Quote)
            .join(
                Quote,
                (Quote.fund_code == Prediction.fund_code) & (Quote.as_of == Prediction.as_of),
            )
            .where(
                Prediction.horizon == horizon,
                Prediction.as_of >= start_at,
                Prediction.as_of < end_at,
            )
            .order_by(Prediction.as_of.asc())
        )
    )

    y_true: list[int] = []
    y_prob: list[float] = []
    y_pred: list[int] = []
    strategy_returns: list[float] = []

    for pred, quote in rows:
        truth = 1 if quote.daily_change_pct > 0 else 0
        pred_up = 1 if pred.up_probability >= 0.5 else 0
        direction = 1.0 if pred.expected_return_pct >= 0 else -1.0
        strategy_r = direction * quote.daily_change_pct / 100.0

        y_true.append(truth)
        y_prob.append(float(pred.up_probability))
        y_pred.append(pred_up)
        strategy_returns.append(strategy_r)

    accuracy, precision, recall, f1 = _classification_metrics(y_true, y_pred)
    auc = _auc_score(y_true, y_prob)
    annualized, max_drawdown, sharpe = _strategy_metrics(strategy_returns)

    existing = db.scalar(
        select(ModelBacktestReport).where(
            ModelBacktestReport.horizon == horizon,
            ModelBacktestReport.report_date == target_date,
        )
    )

    if not existing:
        existing = ModelBacktestReport(
            horizon=horizon,
            report_date=target_date,
        )
        db.add(existing)

    existing.generated_at = datetime.now(tz=UTC).replace(tzinfo=None)
    existing.window_days = window_days
    existing.model_version = _model_version_by_horizon(horizon)
    existing.accuracy = accuracy
    existing.auc = auc
    existing.precision = precision
    existing.recall = recall
    existing.f1 = f1
    existing.annualized_return = annualized
    existing.max_drawdown = max_drawdown
    existing.sharpe = sharpe
    existing.sample_size = len(y_true)

    db.commit()
    db.refresh(existing)
    return existing
