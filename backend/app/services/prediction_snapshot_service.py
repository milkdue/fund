from __future__ import annotations

import hashlib
import json
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import PredictionSnapshot


def _build_snapshot_id(
    *,
    fund_code: str,
    horizon: str,
    as_of: datetime,
    model_version: str,
    feature_payload: dict,
) -> str:
    canonical = json.dumps(
        {
            "fund_code": fund_code,
            "horizon": horizon,
            "as_of": as_of.isoformat(),
            "model_version": model_version,
            "feature_payload": feature_payload,
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:24]


def upsert_prediction_snapshot(
    db: Session,
    *,
    fund_code: str,
    horizon: str,
    as_of: datetime,
    model_version: str,
    data_source: str,
    feature_payload: dict,
) -> PredictionSnapshot:
    PredictionSnapshot.__table__.create(bind=db.get_bind(), checkfirst=True)

    existing = db.scalar(
        select(PredictionSnapshot).where(
            PredictionSnapshot.fund_code == fund_code,
            PredictionSnapshot.horizon == horizon,
            PredictionSnapshot.as_of == as_of,
        )
    )
    snapshot_id = _build_snapshot_id(
        fund_code=fund_code,
        horizon=horizon,
        as_of=as_of,
        model_version=model_version,
        feature_payload=feature_payload,
    )
    payload_json = json.dumps(feature_payload, ensure_ascii=False, sort_keys=True)
    if existing:
        existing.snapshot_id = snapshot_id
        existing.model_version = model_version
        existing.data_source = data_source
        existing.feature_payload_json = payload_json
        return existing

    row = PredictionSnapshot(
        snapshot_id=snapshot_id,
        fund_code=fund_code,
        horizon=horizon,
        as_of=as_of,
        model_version=model_version,
        data_source=data_source,
        feature_payload_json=payload_json,
    )
    db.add(row)
    return row


def latest_snapshot(db: Session, *, fund_code: str, horizon: str) -> PredictionSnapshot | None:
    PredictionSnapshot.__table__.create(bind=db.get_bind(), checkfirst=True)
    return db.scalar(
        select(PredictionSnapshot)
        .where(
            PredictionSnapshot.fund_code == fund_code,
            PredictionSnapshot.horizon == horizon,
        )
        .order_by(PredictionSnapshot.as_of.desc(), PredictionSnapshot.created_at.desc())
        .limit(1)
    )
