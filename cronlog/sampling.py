"""Run sampling utilities for cronlog.

Provides functions to sample job runs by rate, count, or interval,
useful for reducing data volume in high-frequency cron environments.
"""

from __future__ import annotations

import random
from typing import List, Optional
from datetime import timedelta

from cronlog.models import JobRun


def sample_by_rate(runs: List[JobRun], rate: float) -> List[JobRun]:
    """Return a random sample of runs keeping approximately `rate` fraction.

    Args:
        runs: List of JobRun objects.
        rate: Float between 0.0 and 1.0 (inclusive).

    Returns:
        Sampled list of JobRun objects.
    """
    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"rate must be between 0.0 and 1.0, got {rate}")
    if rate == 1.0:
        return list(runs)
    if rate == 0.0:
        return []
    return [r for r in runs if random.random() < rate]


def sample_by_count(runs: List[JobRun], n: int) -> List[JobRun]:
    """Return up to `n` randomly sampled runs.

    Args:
        runs: List of JobRun objects.
        n: Maximum number of runs to return.

    Returns:
        Sampled list of at most n JobRun objects.
    """
    if n < 0:
        raise ValueError(f"n must be non-negative, got {n}")
    if n == 0 or not runs:
        return []
    return random.sample(runs, min(n, len(runs)))


def sample_by_interval(runs: List[JobRun], every_n: int) -> List[JobRun]:
    """Return every nth run from the list (deterministic).

    Args:
        runs: List of JobRun objects.
        every_n: Keep one run every `every_n` runs.

    Returns:
        Sampled list of JobRun objects.
    """
    if every_n < 1:
        raise ValueError(f"every_n must be >= 1, got {every_n}")
    return runs[::every_n]


def sample_by_job(runs: List[JobRun], rate: float) -> List[JobRun]:
    """Sample runs per job name at the given rate, preserving representation.

    Args:
        runs: List of JobRun objects.
        rate: Float between 0.0 and 1.0.

    Returns:
        Sampled list maintaining proportional representation per job.
    """
    from collections import defaultdict

    if not 0.0 <= rate <= 1.0:
        raise ValueError(f"rate must be between 0.0 and 1.0, got {rate}")

    by_job: dict = defaultdict(list)
    for run in runs:
        by_job[run.job_name].append(run)

    result: List[JobRun] = []
    for job_runs in by_job.values():
        result.extend(sample_by_rate(job_runs, rate))
    return result
