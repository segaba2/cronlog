"""Cluster job runs by similarity in duration, exit code, and status."""

from __future__ import annotations

from typing import Dict, List, Optional

from cronlog.models import JobRun, JobStatus


def _duration_seconds(run: JobRun) -> Optional[float]:
    if run.started_at is None or run.finished_at is None:
        return None
    return (run.finished_at - run.started_at).total_seconds()


def cluster_by_duration_bucket(runs: List[JobRun], bucket_size: float = 60.0) -> Dict[str, List[JobRun]]:
    """Group runs into duration buckets of `bucket_size` seconds."""
    result: Dict[str, List[JobRun]] = {}
    for run in runs:
        duration = _duration_seconds(run)
        if duration is None:
            key = "unknown"
        else:
            bucket_index = int(duration // bucket_size)
            low = bucket_index * bucket_size
            high = low + bucket_size
            key = f"{low:.0f}s-{high:.0f}s"
        result.setdefault(key, []).append(run)
    return result


def cluster_by_outcome(runs: List[JobRun]) -> Dict[str, List[JobRun]]:
    """Group runs by (status, exit_code) pair."""
    result: Dict[str, List[JobRun]] = {}
    for run in runs:
        status_label = run.status.value if run.status else "unknown"
        exit_code = run.exit_code if run.exit_code is not None else "none"
        key = f"{status_label}:{exit_code}"
        result.setdefault(key, []).append(run)
    return result


def cluster_by_job_and_status(runs: List[JobRun]) -> Dict[str, List[JobRun]]:
    """Group runs by job name and status."""
    result: Dict[str, List[JobRun]] = {}
    for run in runs:
        status_label = run.status.value if run.status else "unknown"
        key = f"{run.job_name}:{status_label}"
        result.setdefault(key, []).append(run)
    return result


def find_similar_runs(
    target: JobRun,
    runs: List[JobRun],
    duration_tolerance: float = 30.0,
) -> List[JobRun]:
    """Return runs similar to `target` by status, exit code, and duration."""
    target_duration = _duration_seconds(target)
    similar = []
    for run in runs:
        if run.run_id == target.run_id:
            continue
        if run.status != target.status:
            continue
        if run.exit_code != target.exit_code:
            continue
        run_duration = _duration_seconds(run)
        if target_duration is None and run_duration is None:
            similar.append(run)
        elif target_duration is not None and run_duration is not None:
            if abs(run_duration - target_duration) <= duration_tolerance:
                similar.append(run)
    return similar
