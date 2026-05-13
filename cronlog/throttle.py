"""Throttle: prevent a job from being recorded more than once within a cooldown window."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from cronlog.models import JobRun, JobStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def last_run_for_job(runs: List[JobRun], job_name: str) -> Optional[JobRun]:
    """Return the most recent run for *job_name*, or None."""
    matching = [
        r for r in runs
        if r.job_name == job_name and r.started_at is not None
    ]
    if not matching:
        return None
    return max(matching, key=lambda r: r.started_at)  # type: ignore[arg-type]


def is_throttled(
    runs: List[JobRun],
    job_name: str,
    cooldown_seconds: int,
    *,
    now: Optional[datetime] = None,
) -> bool:
    """Return True if *job_name* ran within the last *cooldown_seconds* seconds."""
    if cooldown_seconds <= 0:
        return False
    if now is None:
        now = _utcnow()
    last = last_run_for_job(runs, job_name)
    if last is None:
        return False
    started = last.started_at
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    age = (now - started).total_seconds()
    return age < cooldown_seconds


def filter_throttled_runs(
    runs: List[JobRun],
    cooldown_seconds: int,
    *,
    now: Optional[datetime] = None,
) -> List[JobRun]:
    """Return only the runs that are NOT within the cooldown window of a later run.

    Useful for deduplicating a batch of runs before storage: for each job, keep
    only the latest run when multiple runs fall within *cooldown_seconds* of each other.
    """
    if now is None:
        now = _utcnow()
    if cooldown_seconds <= 0:
        return list(runs)

    by_job: dict[str, List[JobRun]] = {}
    for run in runs:
        by_job.setdefault(run.job_name, []).append(run)

    result: List[JobRun] = []
    for job_runs in by_job.values():
        sorted_runs = sorted(
            job_runs,
            key=lambda r: r.started_at or datetime.min.replace(tzinfo=timezone.utc),
        )
        kept: List[JobRun] = []
        for run in sorted_runs:
            if not kept:
                kept.append(run)
                continue
            prev = kept[-1]
            prev_started = prev.started_at
            curr_started = run.started_at
            if prev_started and curr_started:
                if prev_started.tzinfo is None:
                    prev_started = prev_started.replace(tzinfo=timezone.utc)
                if curr_started.tzinfo is None:
                    curr_started = curr_started.replace(tzinfo=timezone.utc)
                gap = (curr_started - prev_started).total_seconds()
                if gap < cooldown_seconds:
                    kept[-1] = run  # replace with the newer run
                    continue
            kept.append(run)
        result.extend(kept)
    return result
