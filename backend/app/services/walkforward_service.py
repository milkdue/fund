from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from math import sqrt

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Prediction, Quote


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


def _classification_metrics(y_true: list[int], y_pred: list[int]) -> tuple[float, float]:
    if not y_true:
        return 0.0, 0.0

    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    accuracy = (tp + tn) / len(y_true)
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return round(accuracy, 4), round(f1, 4)


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


def _window_metrics(rows: list[tuple[Prediction, Quote]]) -> dict:
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

    accuracy, f1 = _classification_metrics(y_true, y_pred)
    auc = _auc_score(y_true, y_prob)
    annualized, max_drawdown, sharpe = _strategy_metrics(strategy_returns)

    return {
        "sample_size": len(y_true),
        "accuracy": accuracy,
        "auc": auc,
        "f1": f1,
        "annualized_return": annualized,
        "max_drawdown": max_drawdown,
        "sharpe": sharpe,
    }


def build_walkforward_report(
    db: Session,
    *,
    horizon: str,
    window_days: int = 120,
    step_days: int = 14,
    max_windows: int = 12,
) -> dict:
    now = datetime.now(tz=UTC).replace(tzinfo=None)
    today = now.date()
    lookback_days = max(window_days + step_days * max_windows + 30, 120)
    start_at = datetime.combine(today - timedelta(days=lookback_days), time.min)
    end_at = datetime.combine(today + timedelta(days=1), time.min)

    joined_rows = list(
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

    if not joined_rows:
        return {
            "horizon": horizon,
            "generated_at": now,
            "window_days": window_days,
            "step_days": step_days,
            "window_count": 0,
            "avg_accuracy": 0.0,
            "avg_auc": 0.5,
            "avg_f1": 0.0,
            "avg_annualized_return": 0.0,
            "worst_max_drawdown": 0.0,
            "avg_sharpe": 0.0,
            "windows": [],
        }

    trading_days = sorted({pred.as_of.date() for pred, _ in joined_rows})
    windows: list[dict] = []
    last_window_end = None

    for end_day in trading_days:
        if last_window_end and (end_day - last_window_end).days < step_days:
            continue

        start_day = end_day - timedelta(days=window_days)
        bucket = [(pred, quote) for pred, quote in joined_rows if start_day < pred.as_of.date() <= end_day]
        if len(bucket) < 10:
            continue

        metrics = _window_metrics(bucket)
        windows.append(
            {
                "window_start": start_day.isoformat(),
                "window_end": end_day.isoformat(),
                "sample_size": metrics["sample_size"],
                "accuracy": metrics["accuracy"],
                "auc": metrics["auc"],
                "f1": metrics["f1"],
                "annualized_return": metrics["annualized_return"],
                "max_drawdown": metrics["max_drawdown"],
                "sharpe": metrics["sharpe"],
            }
        )
        last_window_end = end_day

    if len(windows) > max_windows:
        windows = windows[-max_windows:]

    if not windows:
        return {
            "horizon": horizon,
            "generated_at": now,
            "window_days": window_days,
            "step_days": step_days,
            "window_count": 0,
            "avg_accuracy": 0.0,
            "avg_auc": 0.5,
            "avg_f1": 0.0,
            "avg_annualized_return": 0.0,
            "worst_max_drawdown": 0.0,
            "avg_sharpe": 0.0,
            "windows": [],
        }

    n = len(windows)
    avg_accuracy = round(sum(w["accuracy"] for w in windows) / n, 4)
    avg_auc = round(sum(w["auc"] for w in windows) / n, 4)
    avg_f1 = round(sum(w["f1"] for w in windows) / n, 4)
    avg_ann = round(sum(w["annualized_return"] for w in windows) / n, 4)
    worst_drawdown = round(min(w["max_drawdown"] for w in windows), 4)
    avg_sharpe = round(sum(w["sharpe"] for w in windows) / n, 4)

    return {
        "horizon": horizon,
        "generated_at": now,
        "window_days": window_days,
        "step_days": step_days,
        "window_count": n,
        "avg_accuracy": avg_accuracy,
        "avg_auc": avg_auc,
        "avg_f1": avg_f1,
        "avg_annualized_return": avg_ann,
        "worst_max_drawdown": worst_drawdown,
        "avg_sharpe": avg_sharpe,
        "windows": windows,
    }
