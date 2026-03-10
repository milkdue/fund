from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.entities import PredictionABResult


def _winner(baseline_expected: float, candidate_expected: float) -> str:
    if candidate_expected > baseline_expected:
        return "candidate"
    if candidate_expected < baseline_expected:
        return "baseline"
    return "tie"


def candidate_version(horizon: str) -> str:
    return settings.model_candidate_short_version if horizon == "short" else settings.model_candidate_mid_version


def baseline_version(horizon: str) -> str:
    return settings.model_short_version if horizon == "short" else settings.model_mid_version


def upsert_ab_result(
    db: Session,
    *,
    fund_code: str,
    horizon: str,
    as_of,
    baseline_up_probability: float,
    baseline_expected_return_pct: float,
    candidate_up_probability: float,
    candidate_expected_return_pct: float,
    actual_return_pct: float | None,
) -> PredictionABResult:
    cand_ver = candidate_version(horizon)
    row = db.scalar(
        select(PredictionABResult).where(
            PredictionABResult.fund_code == fund_code,
            PredictionABResult.horizon == horizon,
            PredictionABResult.as_of == as_of,
            PredictionABResult.candidate_model_version == cand_ver,
        )
    )
    if not row:
        row = PredictionABResult(
            fund_code=fund_code,
            horizon=horizon,
            as_of=as_of,
            baseline_model_version=baseline_version(horizon),
            candidate_model_version=cand_ver,
            baseline_up_probability=baseline_up_probability,
            candidate_up_probability=candidate_up_probability,
            baseline_expected_return_pct=baseline_expected_return_pct,
            candidate_expected_return_pct=candidate_expected_return_pct,
            actual_return_pct=actual_return_pct,
            winner=_winner(baseline_expected_return_pct, candidate_expected_return_pct),
        )
        db.add(row)
    else:
        row.baseline_model_version = baseline_version(horizon)
        row.baseline_up_probability = baseline_up_probability
        row.candidate_up_probability = candidate_up_probability
        row.baseline_expected_return_pct = baseline_expected_return_pct
        row.candidate_expected_return_pct = candidate_expected_return_pct
        row.actual_return_pct = actual_return_pct
        row.winner = _winner(baseline_expected_return_pct, candidate_expected_return_pct)
    return row
