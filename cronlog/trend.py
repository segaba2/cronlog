"""Trend analysis for job run durations and failure rates over time."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Optional


def _duration_seconds(run) -> Optional[float]:
    if run.get("started_at") and run.get("finished_at"):
        start = datetime.fromisoformat(run["started_at"])
        end = datetime.fromisoformat(run["finished_at"])
        return (end - start).total_seconds()
    return None


def _week_bucket(run) -> str:
    """Return ISO year-week string for a run, e.g. '2024-W03'."""
    dt = datetime.fromisoformat(run["started_at"])
    year, week, _ = dt.isocalendar()
    return f"{year}-W{week:02d}"


def _day_bucket(run) -> str:
    dt = datetime.fromisoformat(run["started_at"])
    return dt.strftime("%Y-%m-%d")


def duration_trend(runs: List[dict], bucket: str = "day") -> Dict[str, float]:
    """Return average duration per time bucket (day or week)."""
    bucketer = _week_bucket if bucket == "week" else _day_bucket
    totals: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    for run in runs:
        dur = _duration_seconds(run)
        if dur is None:
            continue
        key = bucketer(run)
        totals[key] = totals.get(key, 0.0) + dur
        counts[key] = counts.get(key, 0) + 1
    return {k: totals[k] / counts[k] for k in sorted(totals)}


def failure_rate_trend(runs: List[dict], bucket: str = "day") -> Dict[str, float]:
    """Return failure rate (0.0–1.0) per time bucket."""
    bucketer = _week_bucket if bucket == "week" else _day_bucket
    totals: Dict[str, int] = {}
    failures: Dict[str, int] = {}
    for run in runs:
        key = bucketer(run)
        totals[key] = totals.get(key, 0) + 1
        if run.get("status") == "failure":
            failures[key] = failures.get(key, 0) + 1
    return {
        k: failures.get(k, 0) / totals[k]
        for k in sorted(totals)
    }


def run_count_trend(runs: List[dict], bucket: str = "day") -> Dict[str, int]:
    """Return total run count per time bucket."""
    bucketer = _week_bucket if bucket == "week" else _day_bucket
    counts: Dict[str, int] = {}
    for run in runs:
        key = bucketer(run)
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))
