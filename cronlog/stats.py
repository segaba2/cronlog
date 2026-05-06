from typing import List, Dict, Any
from cronlog.models import JobRun, JobStatus
from datetime import timedelta


def compute_stats(runs: List[JobRun]) -> Dict[str, Any]:
    """Compute aggregate statistics over a list of job runs."""
    if not runs:
        return {
            "total": 0,
            "success": 0,
            "failure": 0,
            "success_rate": None,
            "avg_duration_seconds": None,
            "min_duration_seconds": None,
            "max_duration_seconds": None,
        }

    total = len(runs)
    successes = [r for r in runs if r.status == JobStatus.SUCCESS]
    failures = [r for r in runs if r.status == JobStatus.FAILURE]

    durations = [
        r.duration_seconds
        for r in runs
        if r.duration_seconds is not None
    ]

    return {
        "total": total,
        "success": len(successes),
        "failure": len(failures),
        "success_rate": round(len(successes) / total * 100, 2) if total else None,
        "avg_duration_seconds": round(sum(durations) / len(durations), 3) if durations else None,
        "min_duration_seconds": round(min(durations), 3) if durations else None,
        "max_duration_seconds": round(max(durations), 3) if durations else None,
    }


def compute_stats_by_job(runs: List[JobRun]) -> Dict[str, Dict[str, Any]]:
    """Compute per-job statistics from a list of runs."""
    jobs: Dict[str, List[JobRun]] = {}
    for run in runs:
        jobs.setdefault(run.job_name, []).append(run)
    return {job_name: compute_stats(job_runs) for job_name, job_runs in jobs.items()}
