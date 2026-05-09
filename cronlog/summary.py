"""Generates human-readable summary reports for job run history."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict, Any

from cronlog.models import JobRun, JobStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def summarise_runs(runs: List[JobRun]) -> Dict[str, Any]:
    """Return a top-level summary dict for a list of runs."""
    if not runs:
        return {
            "total": 0,
            "success": 0,
            "failure": 0,
            "timeout": 0,
            "running": 0,
            "success_rate": None,
            "jobs": [],
        }

    total = len(runs)
    success = sum(1 for r in runs if r.status == JobStatus.SUCCESS)
    failure = sum(1 for r in runs if r.status == JobStatus.FAILURE)
    timeout = sum(1 for r in runs if r.status == JobStatus.TIMEOUT)
    running = sum(1 for r in runs if r.status == JobStatus.RUNNING)

    finished = [r for r in runs if r.duration_seconds is not None]
    avg_duration = (
        sum(r.duration_seconds for r in finished) / len(finished)
        if finished
        else None
    )

    success_rate = round(success / total * 100, 1) if total else None

    job_names = sorted({r.job_name for r in runs})

    return {
        "total": total,
        "success": success,
        "failure": failure,
        "timeout": timeout,
        "running": running,
        "success_rate": success_rate,
        "avg_duration_seconds": avg_duration,
        "jobs": job_names,
    }


def summarise_by_job(runs: List[JobRun]) -> Dict[str, Dict[str, Any]]:
    """Return per-job summary dicts keyed by job name."""
    by_job: Dict[str, List[JobRun]] = {}
    for run in runs:
        by_job.setdefault(run.job_name, []).append(run)

    return {name: summarise_runs(job_runs) for name, job_runs in sorted(by_job.items())}


def format_summary(summary: Dict[str, Any]) -> str:
    """Render a top-level summary dict as a printable string."""
    rate = (
        f"{summary['success_rate']}%" if summary["success_rate"] is not None else "n/a"
    )
    avg = (
        f"{summary['avg_duration_seconds']:.1f}s"
        if summary.get("avg_duration_seconds") is not None
        else "n/a"
    )
    lines = [
        f"Total runs   : {summary['total']}",
        f"Success      : {summary['success']}",
        f"Failure      : {summary['failure']}",
        f"Timeout      : {summary['timeout']}",
        f"Running      : {summary['running']}",
        f"Success rate : {rate}",
        f"Avg duration : {avg}",
    ]
    if summary["jobs"]:
        lines.append("Jobs         : " + ", ".join(summary["jobs"]))
    return "\n".join(lines)
