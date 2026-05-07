"""Retention policy: prune old job run records from storage."""

from datetime import datetime, timezone, timedelta
from typing import List, Optional

from cronlog.models import JobRun
from cronlog.storage import JobRunStorage


def prune_by_age(runs: List[JobRun], max_age_days: int) -> List[JobRun]:
    """Return runs that are newer than max_age_days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    return [r for r in runs if r.started_at >= cutoff]


def prune_by_count(runs: List[JobRun], max_count: int) -> List[JobRun]:
    """Return the most recent max_count runs, sorted by started_at."""
    sorted_runs = sorted(runs, key=lambda r: r.started_at, reverse=True)
    return sorted_runs[:max_count]


def prune_by_job_count(runs: List[JobRun], max_per_job: int) -> List[JobRun]:
    """Return at most max_per_job runs per job name, keeping the most recent."""
    from collections import defaultdict
    buckets: dict = defaultdict(list)
    for run in runs:
        buckets[run.job_name].append(run)
    result = []
    for job_runs in buckets.values():
        sorted_job = sorted(job_runs, key=lambda r: r.started_at, reverse=True)
        result.extend(sorted_job[:max_per_job])
    return result


def apply_retention(
    storage: JobRunStorage,
    max_age_days: Optional[int] = None,
    max_count: Optional[int] = None,
    max_per_job: Optional[int] = None,
) -> int:
    """Apply retention policies and persist. Returns number of pruned runs."""
    runs = storage.load_all()
    original_count = len(runs)

    if max_age_days is not None:
        runs = prune_by_age(runs, max_age_days)
    if max_per_job is not None:
        runs = prune_by_job_count(runs, max_per_job)
    if max_count is not None:
        runs = prune_by_count(runs, max_count)

    storage.save_all(runs)
    return original_count - len(runs)
