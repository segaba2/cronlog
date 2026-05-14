"""Group job runs by various dimensions for analysis."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Dict, List, Optional

from cronlog.models import JobRun, JobStatus


def group_by_job_name(runs: List[JobRun]) -> Dict[str, List[JobRun]]:
    """Group runs by their job name."""
    groups: Dict[str, List[JobRun]] = defaultdict(list)
    for run in runs:
        groups[run.job_name].append(run)
    return dict(groups)


def group_by_status(runs: List[JobRun]) -> Dict[str, List[JobRun]]:
    """Group runs by their status value."""
    groups: Dict[str, List[JobRun]] = defaultdict(list)
    for run in runs:
        groups[run.status.value].append(run)
    return dict(groups)


def group_by_date(runs: List[JobRun], fmt: str = "%Y-%m-%d") -> Dict[str, List[JobRun]]:
    """Group runs by the date they started, using *fmt* as the key format."""
    groups: Dict[str, List[JobRun]] = defaultdict(list)
    for run in runs:
        key = run.started_at.strftime(fmt)
        groups[key].append(run)
    return dict(groups)


def group_by_hour(runs: List[JobRun]) -> Dict[str, List[JobRun]]:
    """Group runs by the UTC hour they started (key: 'YYYY-MM-DD HH')."""
    return group_by_date(runs, fmt="%Y-%m-%d %H")


def group_by_exit_code(runs: List[JobRun]) -> Dict[Optional[int], List[JobRun]]:
    """Group runs by their exit code (None for still-running jobs)."""
    groups: Dict[Optional[int], List[JobRun]] = defaultdict(list)
    for run in runs:
        groups[run.exit_code].append(run)
    return dict(groups)


def summarise_groups(groups: Dict[str, List[JobRun]]) -> Dict[str, Dict[str, int]]:
    """Return per-group counts of total, success and failure runs."""
    summary: Dict[str, Dict[str, int]] = {}
    for key, group_runs in groups.items():
        total = len(group_runs)
        success = sum(1 for r in group_runs if r.status == JobStatus.SUCCESS)
        failure = sum(1 for r in group_runs if r.status == JobStatus.FAILURE)
        summary[str(key)] = {"total": total, "success": success, "failure": failure}
    return summary
