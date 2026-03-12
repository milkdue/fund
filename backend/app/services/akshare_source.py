from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from importlib import import_module
from statistics import pstdev

from app.core.config import settings
from app.services.time_utils import shanghai_now_naive


@dataclass
class AkshareNavSnapshot:
    code: str
    name: str
    as_of: datetime
    nav: float
    daily_change_pct: float
    volatility_20d: float
    source: str = "akshare_fund_open_fund_info_em"


class AkshareSourceError(Exception):
    pass


class AkshareUnavailableError(AkshareSourceError):
    pass


def _normalize_column_name(name: str) -> str:
    return str(name).strip().replace(" ", "")


def _to_float(value) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace("%", "")
    if not text or text.lower() == "nan":
        return None
    try:
        return float(text)
    except Exception:
        return None


def _calc_volatility_20d(net_values: list[float]) -> float:
    window = net_values[-21:]
    if len(window) < 3:
        return 0.0
    returns: list[float] = []
    for idx in range(1, len(window)):
        prev = window[idx - 1]
        curr = window[idx]
        if prev == 0:
            continue
        returns.append((curr - prev) / prev * 100)
    if len(returns) < 2:
        return 0.0
    return round(pstdev(returns), 2)


def fetch_open_fund_nav_snapshot(code: str) -> AkshareNavSnapshot:
    if not settings.akshare_enabled:
        raise AkshareUnavailableError("akshare disabled")

    try:
        akshare = import_module("akshare")
    except Exception as exc:
        raise AkshareUnavailableError(f"akshare import failed: {exc}") from exc

    fetcher = getattr(akshare, "fund_open_fund_info_em", None)
    if fetcher is None:
        raise AkshareSourceError("fund_open_fund_info_em is unavailable")

    try:
        df = fetcher(symbol=code, indicator="单位净值走势")
    except Exception as exc:
        raise AkshareSourceError(f"akshare request failed: {exc}") from exc

    if df is None or getattr(df, "empty", True):
        raise AkshareSourceError("akshare returned empty dataframe")

    rows = df.rename(columns={col: _normalize_column_name(col) for col in df.columns})
    date_col = next((c for c in rows.columns if c in {"净值日期", "日期"}), None)
    nav_col = next((c for c in rows.columns if c in {"单位净值", "单位净值走势", "累计净值"}), None)
    change_col = next((c for c in rows.columns if c in {"日增长率", "涨跌幅"}), None)

    if not date_col or not nav_col:
        raise AkshareSourceError(f"unexpected akshare columns: {list(rows.columns)}")

    values: list[tuple[datetime, float, float | None]] = []
    for _, row in rows.tail(90).iterrows():
        try:
            dt = datetime.combine(datetime.strptime(str(row[date_col])[:10], "%Y-%m-%d").date(), time(hour=15))
        except Exception:
            continue
        nav = _to_float(row[nav_col])
        if nav is None:
            continue
        change = _to_float(row[change_col]) if change_col else None
        values.append((dt, nav, change))

    if not values:
        raise AkshareSourceError("akshare returned no valid nav rows")

    values.sort(key=lambda item: item[0])
    net_values = [item[1] for item in values]
    last_dt, last_nav, last_change = values[-1]
    if last_change is None:
        if len(net_values) >= 2 and net_values[-2] != 0:
            last_change = round((net_values[-1] - net_values[-2]) / net_values[-2] * 100, 2)
        else:
            last_change = 0.0

    name = f"基金{code}"
    latest_dt = min(last_dt, shanghai_now_naive())
    return AkshareNavSnapshot(
        code=code,
        name=name,
        as_of=latest_dt,
        nav=round(last_nav, 4),
        daily_change_pct=round(last_change, 2),
        volatility_20d=_calc_volatility_20d(net_values),
    )
