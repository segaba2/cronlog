"""Ranking utilities for job runs based on various scoring criteria."""

from __future__ import annotations

from typing import List, Tuple

from cronlog.models import JobRun, JobStatus


def _duration_seconds(run: JobRun) -> float:
    """Return duration in seconds, or 0.0 if run is unfinished."""
    if run.started_at is None or run.finished_at is None:
        return 0.0
    return (run.finished_at - run.started_at).total_seconds()


def rank_by_duration(runs: List[JobRun], descending: bool = True) -> List[Tuple[int, JobRun]]:
    """Return runs ranked by duration (longest first by default).

    Returns a list of (rank, run) tuples starting at rank 1.
    """
    finished = [r for r in runs if r.finished_at is not None]
    sorted_runs = sorted(finished, key=_duration_seconds, reverse=descending)
    return [(i + 1, run) for i, run in enumerate(sorted_runs)]


def rank_by_failure_rate(runs: List[JobRun]) -> List[Tuple[str, float, int]]:
    """Rank job names by their failure rate (highest first).

    Returns a list of (job_name, failure_rate, total_runs) tuples.
    """
    counts: dict[str, dict] = {}
    for run in runs:
        name = run.job_name
        if name not in counts:
            counts[name] = {"total": 0, "failures": 0}
        counts[name]["total"] += 1
        if run.status == JobStatus.FAILURE:
            counts[name]["failures"] += 1

    ranked = [
        (name, data["failures"] / data["total"], data["total"])
        for name, data in counts.items()
        if data["total"] > 0
    ]
    ranked.sort(key=lambda t: t[1], reverse=True)
    return ranked


def rank_by_run_count(runs: List[JobRun]) -> List[Tuple[str, int]]:
    """Rank job names by total number of runs (most frequent first).

    Returns a list of (job_name, run_count) tuples.
    """
    counts: dict[str, int] = {}
    for run in runs:
        counts[run.job_name] = counts.get(run.job_name, 0) + 1
    ranked = sorted(counts.items(), key=lambda t: t[1], reverse=True)
    return ranked


def top_n(ranked: list, n: int) -> list:
    """Return the first *n* entries from a ranked list."""
    return ranked[:n]
