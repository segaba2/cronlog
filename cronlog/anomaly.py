"""Anomaly detection for job runs based on duration and failure patterns."""

from __future__ import annotations

from typing import List, Optional

from cronlog.models import JobRun, JobStatus


def _duration_seconds(run: JobRun) -> Optional[float]:
    if run.started_at is None or run.finished_at is None:
        return None
    return (run.finished_at - run.started_at).total_seconds()


def compute_mean_stddev(values: List[float]):
    """Return (mean, stddev) for a list of floats. Returns (0, 0) for empty."""
    if not values:
        return 0.0, 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return mean, variance ** 0.5


def detect_duration_anomalies(
    runs: List[JobRun],
    z_threshold: float = 2.0,
) -> List[JobRun]:
    """Return runs whose duration deviates more than z_threshold standard
    deviations from the mean duration for that job."""
    from collections import defaultdict

    by_job: dict = defaultdict(list)
    for run in runs:
        d = _duration_seconds(run)
        if d is not None:
            by_job[run.job_name].append((run, d))

    anomalies: List[JobRun] = []
    for job_runs in by_job.values():
        durations = [d for _, d in job_runs]
        mean, stddev = compute_mean_stddev(durations)
        if stddev == 0:
            continue
        for run, d in job_runs:
            if abs(d - mean) / stddev > z_threshold:
                anomalies.append(run)
    return anomalies


def detect_failure_bursts(
    runs: List[JobRun],
    window: int = 5,
    min_failures: int = 3,
) -> List[JobRun]:
    """Return runs that are part of a failure burst: at least min_failures
    failures within any sliding window of *window* consecutive runs per job."""
    from collections import defaultdict

    by_job: dict = defaultdict(list)
    for run in runs:
        by_job[run.job_name].append(run)

    burst_runs: List[JobRun] = []
    for job_runs in by_job.values():
        sorted_runs = sorted(job_runs, key=lambda r: r.started_at or 0)
        n = len(sorted_runs)
        for i in range(n - window + 1):
            chunk = sorted_runs[i : i + window]
            failures = [r for r in chunk if r.status == JobStatus.FAILURE]
            if len(failures) >= min_failures:
                for r in failures:
                    if r not in burst_runs:
                        burst_runs.append(r)
    return burst_runs


def anomaly_report(runs: List[JobRun], z_threshold: float = 2.0) -> dict:
    """Return a summary dict with duration anomalies and failure bursts."""
    duration_anomalies = detect_duration_anomalies(runs, z_threshold)
    failure_bursts = detect_failure_bursts(runs)
    return {
        "duration_anomalies": duration_anomalies,
        "failure_bursts": failure_bursts,
        "total_anomalies": len(set(duration_anomalies) | set(failure_bursts)),
    }
