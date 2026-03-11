from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


SHANGHAI_TZ = ZoneInfo("Asia/Shanghai")


def shanghai_now_naive() -> datetime:
    return datetime.now(tz=SHANGHAI_TZ).replace(tzinfo=None)


def epoch_ms_to_shanghai_naive(timestamp_ms: int) -> datetime:
    return datetime.fromtimestamp(timestamp_ms / 1000, tz=SHANGHAI_TZ).replace(tzinfo=None)
