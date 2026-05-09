"""Compute per-job runtime metrics such as avg/min/max duration."""

from __future__ import annotations

from typing import Dict, List

from cronlog.models import JobRun, JobStatus


def _duration_seconds(run: JobRun) -> float | None:
    """Return duration in seconds for a finished run, or None."""
    d = run.to_dict()
    return d.get("duration_seconds")


def compute_runtime_metrics(runs: List[JobRun]) -> Dict:
    """Return aggregate runtime metrics for a list of runs.

    Only finished (success or failure) runs with a recorded duration
    are included in duration calculations.
    """
    total = len(runs)
    successes = [r for r in runs if r.status == JobStatus.SUCCESS]
    failures = [r for r in runs if r.status == JobStatus.FAILURE]
    timeouts = [r for r in runs if r.status == JobStatus.TIMEOUT]

    durations = [
        d for r in runs if (d := _duration_seconds(r)) is not None
    ]

    metrics: Dict = {
        "total": total,
        "success_count": len(successes),
        "failure_count": len(failures),
        "timeout_count": len(timeouts),
        "avg_duration_seconds": None,
        "min_duration_seconds": None,
        "max_duration_seconds": None,
    }

    if durations:
        metrics["avg_duration_seconds"] = sum(durations) / len(durations)
        metrics["min_duration_seconds"] = min(durations)
        metrics["max_duration_seconds"] = max(durations)

    return metrics


def compute_runtime_metrics_by_job(runs: List[JobRun]) -> Dict[str, Dict]:
    """Return runtime metrics grouped by job name."""
    groups: Dict[str, List[JobRun]] = {}
    for run in runs:
        groups.setdefault(run.job_name, []).append(run)

    return {job: compute_runtime_metrics(job_runs) for job, job_runs in groups.items()}
