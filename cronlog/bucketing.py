"""Bucket job runs into time-based windows for aggregation and analysis."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from cronlog.models import JobRun


def _bucket_key_minute(dt: datetime, interval_minutes: int) -> str:
    """Return a string key for the interval bucket containing *dt*."""
    floored = dt.replace(
        minute=(dt.minute // interval_minutes) * interval_minutes,
        second=0,
        microsecond=0,
    )
    return floored.strftime("%Y-%m-%dT%H:%M")


def bucket_by_minute_interval(
    runs: List[JobRun], interval_minutes: int = 5
) -> Dict[str, List[JobRun]]:
    """Group runs into fixed-width minute buckets.

    Args:
        runs: List of JobRun objects.
        interval_minutes: Width of each bucket in minutes (default 5).

    Returns:
        Ordered dict mapping bucket key strings to lists of runs.
    """
    if interval_minutes < 1:
        raise ValueError("interval_minutes must be >= 1")

    buckets: Dict[str, List[JobRun]] = defaultdict(list)
    for run in runs:
        key = _bucket_key_minute(run.started_at, interval_minutes)
        buckets[key].append(run)
    return dict(sorted(buckets.items()))


def bucket_by_hour(runs: List[JobRun]) -> Dict[str, List[JobRun]]:
    """Group runs by calendar hour (YYYY-MM-DDTHH)."""
    buckets: Dict[str, List[JobRun]] = defaultdict(list)
    for run in runs:
        key = run.started_at.strftime("%Y-%m-%dT%H")
        buckets[key].append(run)
    return dict(sorted(buckets.items()))


def bucket_by_day(runs: List[JobRun]) -> Dict[str, List[JobRun]]:
    """Group runs by calendar day (YYYY-MM-DD)."""
    buckets: Dict[str, List[JobRun]] = defaultdict(list)
    for run in runs:
        key = run.started_at.strftime("%Y-%m-%d")
        buckets[key].append(run)
    return dict(sorted(buckets.items()))


def bucket_run_counts(
    buckets: Dict[str, List[JobRun]]
) -> Dict[str, int]:
    """Convert a bucket mapping to a simple count per bucket."""
    return {key: len(runs) for key, runs in buckets.items()}


def fill_missing_buckets(
    buckets: Dict[str, List[JobRun]],
    start: datetime,
    end: datetime,
    interval_minutes: int = 60,
) -> Dict[str, List[JobRun]]:
    """Ensure every interval between *start* and *end* is present in the dict.

    Missing buckets are filled with empty lists so callers can rely on a
    contiguous sequence of keys.
    """
    filled: Dict[str, List[JobRun]] = {}
    current = start.replace(second=0, microsecond=0)
    delta = timedelta(minutes=interval_minutes)
    while current <= end:
        key = _bucket_key_minute(current, interval_minutes)
        filled[key] = buckets.get(key, [])
        current += delta
    return filled
