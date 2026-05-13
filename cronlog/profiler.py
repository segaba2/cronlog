"""Run profiling: track and report slow jobs based on historical durations."""

from __future__ import annotations

from typing import Dict, List, Optional

from cronlog.models import JobRun, JobStatus


def _duration_seconds(run: JobRun) -> Optional[float]:
    """Return duration in seconds for a finished run, or None."""
    if run.started_at is None or run.finished_at is None:
        return None
    delta = run.finished_at - run.started_at
    return delta.total_seconds()


def compute_average_duration(runs: List[JobRun]) -> Optional[float]:
    """Return mean duration in seconds across all finished runs."""
    durations = [d for r in runs if (d := _duration_seconds(r)) is not None]
    if not durations:
        return None
    return sum(durations) / len(durations)


def find_slow_runs(
    runs: List[JobRun],
    threshold_seconds: float,
) -> List[JobRun]:
    """Return runs whose duration exceeded *threshold_seconds*."""
    result = []
    for run in runs:
        d = _duration_seconds(run)
        if d is not None and d > threshold_seconds:
            result.append(run)
    return result


def profile_by_job(runs: List[JobRun]) -> Dict[str, dict]:
    """Return per-job profiling stats: count, avg, min, max duration (seconds)."""
    buckets: Dict[str, List[float]] = {}
    for run in runs:
        d = _duration_seconds(run)
        if d is not None:
            buckets.setdefault(run.job_name, []).append(d)

    result: Dict[str, dict] = {}
    for job_name, durations in buckets.items():
        result[job_name] = {
            "count": len(durations),
            "avg_seconds": sum(durations) / len(durations),
            "min_seconds": min(durations),
            "max_seconds": max(durations),
        }
    return result


def slowest_runs(runs: List[JobRun], n: int = 5) -> List[JobRun]:
    """Return the *n* slowest finished runs, longest first."""
    finished = [r for r in runs if _duration_seconds(r) is not None]
    return sorted(finished, key=lambda r: _duration_seconds(r), reverse=True)[:n]
