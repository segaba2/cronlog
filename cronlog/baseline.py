"""Baseline tracking: record and compare expected job durations."""

from __future__ import annotations

import json
import os
from typing import Dict, List, Optional

from cronlog.models import JobRun

_BASELINE_FILENAME = "baselines.json"


def _baseline_path(log_dir: str) -> str:
    return os.path.join(log_dir, _BASELINE_FILENAME)


def _duration_seconds(run: JobRun) -> Optional[float]:
    if run.started_at is None or run.finished_at is None:
        return None
    return (run.finished_at - run.started_at).total_seconds()


def compute_baseline(runs: List[JobRun]) -> Optional[float]:
    """Return the mean duration (seconds) of a list of finished runs."""
    durations = [d for r in runs if (d := _duration_seconds(r)) is not None]
    if not durations:
        return None
    return sum(durations) / len(durations)


def save_baseline(log_dir: str, job_name: str, baseline_seconds: float) -> None:
    """Persist a baseline value for a job."""
    path = _baseline_path(log_dir)
    data: Dict[str, float] = {}
    if os.path.exists(path):
        with open(path, "r") as fh:
            data = json.load(fh)
    data[job_name] = baseline_seconds
    os.makedirs(log_dir, exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)


def load_baseline(log_dir: str, job_name: str) -> Optional[float]:
    """Load the stored baseline for a job, or None if not set."""
    path = _baseline_path(log_dir)
    if not os.path.exists(path):
        return None
    with open(path, "r") as fh:
        data: Dict[str, float] = json.load(fh)
    return data.get(job_name)


def load_all_baselines(log_dir: str) -> Dict[str, float]:
    """Return all stored baselines."""
    path = _baseline_path(log_dir)
    if not os.path.exists(path):
        return {}
    with open(path, "r") as fh:
        return json.load(fh)


def exceeds_baseline(run: JobRun, baseline_seconds: float, threshold: float = 0.2) -> bool:
    """Return True if *run* took more than *threshold* (fraction) over the baseline."""
    duration = _duration_seconds(run)
    if duration is None:
        return False
    return duration > baseline_seconds * (1 + threshold)
