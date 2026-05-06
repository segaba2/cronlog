"""Filtering and querying utilities for JobRun records."""

from datetime import datetime, timezone
from typing import List, Optional

from cronlog.models import JobRun, JobStatus


def filter_by_status(runs: List[JobRun], status: JobStatus) -> List[JobRun]:
    """Return only runs matching the given status."""
    return [r for r in runs if r.status == status]


def filter_by_job_name(runs: List[JobRun], job_name: str) -> List[JobRun]:
    """Return only runs whose job_name matches (case-insensitive)."""
    name_lower = job_name.lower()
    return [r for r in runs if r.job_name.lower() == name_lower]


def filter_since(runs: List[JobRun], since: datetime) -> List[JobRun]:
    """Return only runs that started at or after *since*."""
    if since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    return [r for r in runs if r.started_at >= since]


def filter_until(runs: List[JobRun], until: datetime) -> List[JobRun]:
    """Return only runs that started before or at *until*."""
    if until.tzinfo is None:
        until = until.replace(tzinfo=timezone.utc)
    return [r for r in runs if r.started_at <= until]


def sort_by_started_at(runs: List[JobRun], descending: bool = True) -> List[JobRun]:
    """Return runs sorted by start time."""
    return sorted(runs, key=lambda r: r.started_at, reverse=descending)


def latest_per_job(runs: List[JobRun]) -> List[JobRun]:
    """Return the most recent run for each unique job name."""
    latest: dict = {}
    for run in runs:
        existing = latest.get(run.job_name)
        if existing is None or run.started_at > existing.started_at:
            latest[run.job_name] = run
    return list(latest.values())


def apply_filters(
    runs: List[JobRun],
    job_name: Optional[str] = None,
    status: Optional[JobStatus] = None,
    since: Optional[datetime] = None,
    until: Optional[datetime] = None,
) -> List[JobRun]:
    """Apply multiple optional filters in sequence and return sorted results."""
    result = list(runs)
    if job_name is not None:
        result = filter_by_job_name(result, job_name)
    if status is not None:
        result = filter_by_status(result, status)
    if since is not None:
        result = filter_since(result, since)
    if until is not None:
        result = filter_until(result, until)
    return sort_by_started_at(result)
