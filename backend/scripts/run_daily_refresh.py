from __future__ import annotations

import json
import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.workers.daily_job import run_daily_refresh  # noqa: E402


def _parse_codes(raw: str | None) -> list[str] | None:
    if not raw:
        return None
    codes = [item.strip() for item in raw.split(",") if item.strip()]
    return codes or None


def _write_summary(result: dict) -> None:
    summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return

    lines = [
        "## Daily Refresh Result",
        "",
        f"- status: `{result['status']}`",
        f"- target funds: `{result['target_code_count']}`",
        f"- quote success: `{result['success_count']}`",
        f"- quote coverage: `{result['coverage_rate']}`",
        f"- news success: `{result['news_success_count']}`",
        f"- market status: `{result['market_status']}`",
        f"- elapsed seconds: `{result['elapsed_seconds']}`",
    ]
    if result.get("failed_codes"):
        lines.extend(
            [
                "",
                "### Quote Failures",
                "",
                ", ".join(result["failed_codes"]),
            ]
        )
    if result.get("news_failed_codes"):
        lines.extend(
            [
                "",
                "### News Failures",
                "",
                ", ".join(result["news_failed_codes"]),
            ]
        )

    Path(summary_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    codes = _parse_codes(os.getenv("FUND_REFRESH_CODES"))
    result = run_daily_refresh(codes=codes)
    print(json.dumps(result, ensure_ascii=False))
    _write_summary(result)
    return 1 if result.get("success_count", 0) <= 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
