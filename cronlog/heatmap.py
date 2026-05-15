"""Heatmap module: aggregate run counts by time bucket for visual inspection."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from cronlog.models import JobRun


def _hour_bucket(dt: datetime) -> str:
    """Return an ISO-like string truncated to the hour."""
    return dt.strftime("%Y-%m-%dT%H")


def _weekday_hour_bucket(dt: datetime) -> Tuple[int, int]:
    """Return (weekday 0=Mon, hour) for a datetime."""
    return (dt.weekday(), dt.hour)


def heatmap_by_hour(runs: List[JobRun]) -> Dict[str, int]:
    """Return a mapping of hour-bucket string -> run count."""
    counts: Dict[str, int] = defaultdict(int)
    for run in runs:
        bucket = _hour_bucket(run.started_at)
        counts[bucket] += 1
    return dict(counts)


def heatmap_by_weekday_hour(runs: List[JobRun]) -> Dict[Tuple[int, int], int]:
    """Return a mapping of (weekday, hour) -> run count."""
    counts: Dict[Tuple[int, int], int] = defaultdict(int)
    for run in runs:
        bucket = _weekday_hour_bucket(run.started_at)
        counts[bucket] += 1
    return dict(counts)


def heatmap_by_day(runs: List[JobRun]) -> Dict[str, int]:
    """Return a mapping of date string (YYYY-MM-DD) -> run count."""
    counts: Dict[str, int] = defaultdict(int)
    for run in runs:
        bucket = run.started_at.strftime("%Y-%m-%d")
        counts[bucket] += 1
    return dict(counts)


def format_heatmap(heatmap: Dict[str, int], top_n: int = 10) -> str:
    """Return a simple text representation of the top_n busiest buckets."""
    if not heatmap:
        return "No data."
    sorted_items = sorted(heatmap.items(), key=lambda kv: kv[1], reverse=True)
    lines = [f"{'Bucket':<25} {'Count':>6}"]
    lines.append("-" * 33)
    for bucket, count in sorted_items[:top_n]:
        lines.append(f"{str(bucket):<25} {count:>6}")
    return "\n".join(lines)
