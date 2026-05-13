"""Watchdog module: detect stale/overdue scheduled jobs and emit alerts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from cronlog.schedule import ScheduledJob, load_jobs
from cronlog.storage import JobRunStorage


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def find_overdue_jobs(
    jobs: List[ScheduledJob],
    storage: JobRunStorage,
    grace_seconds: int = 300,
    now: Optional[datetime] = None,
) -> List[dict]:
    """Return a list of overdue job descriptors.

    A job is overdue when its most-recently scheduled run time has passed
    (plus a grace period) but no successful run has been recorded since.
    """
    if now is None:
        now = _utcnow()

    all_runs = storage.load_all()
    overdue = []

    for job in jobs:
        scheduled_at = job.next_run(reference=None)  # last due time
        # Compute the most recent past trigger by walking back one interval
        last_due = _last_due_time(job, now)
        if last_due is None:
            continue

        deadline = last_due.timestamp() + grace_seconds
        if now.timestamp() <= deadline:
            continue

        # Check whether a successful run exists after last_due
        recent_success = any(
            r.job_name == job.name
            and r.status.value == "success"
            and r.started_at is not None
            and r.started_at.timestamp() >= last_due.timestamp()
            for r in all_runs
        )

        if not recent_success:
            overdue.append({
                "job_name": job.name,
                "cron": job.cron,
                "last_due": last_due.isoformat(),
                "grace_seconds": grace_seconds,
            })

    return overdue


def _last_due_time(
    job: ScheduledJob, now: datetime
) -> Optional[datetime]:
    """Return the most recent past scheduled time for *job* relative to *now*."""
    try:
        from croniter import croniter  # type: ignore
    except ImportError:
        return None

    ci = croniter(job.cron, now)
    return ci.get_prev(datetime)


def watchdog_report(
    storage: JobRunStorage,
    log_dir: str,
    grace_seconds: int = 300,
) -> List[dict]:
    """High-level helper: load scheduled jobs and return overdue entries."""
    jobs = load_jobs(log_dir)
    return find_overdue_jobs(jobs, storage, grace_seconds=grace_seconds)
