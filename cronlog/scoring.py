"""Run scoring — assign a numeric health score to job runs and aggregate by job."""

from __future__ import annotations

from typing import Dict, List

from cronlog.models import JobRun, JobStatus

# Weights used when computing the composite score (0-100).
_WEIGHT_STATUS = 50
_WEIGHT_DURATION = 30
_WEIGHT_EXIT_CODE = 20


def _duration_seconds(run: JobRun) -> float:
    """Return wall-clock duration in seconds, or 0 for unfinished runs."""
    if run.started_at is None or run.finished_at is None:
        return 0.0
    return (run.finished_at - run.started_at).total_seconds()


def score_run(run: JobRun, baseline_seconds: float = 0.0) -> float:
    """Return a health score in [0, 100] for a single run.

    Higher is healthier.  The score is composed of:
    - Status component  (50 pts): full points for success, 0 for failure/timeout.
    - Duration component (30 pts): full points when duration <= baseline, linearly
      degrading to 0 when duration >= 3× baseline (or baseline == 0).
    - Exit-code component (20 pts): full points for exit code 0, 0 otherwise.
    """
    # Status component
    if run.status == JobStatus.SUCCESS:
        status_score = _WEIGHT_STATUS
    else:
        status_score = 0.0

    # Duration component
    if baseline_seconds > 0:
        duration = _duration_seconds(run)
        ratio = duration / baseline_seconds  # 1.0 == exactly on baseline
        duration_score = max(0.0, _WEIGHT_DURATION * (1.0 - (ratio - 1.0) / 2.0))
    else:
        duration_score = _WEIGHT_DURATION  # no baseline → neutral

    # Exit-code component
    exit_code_score = _WEIGHT_EXIT_CODE if run.exit_code == 0 else 0.0

    return round(status_score + duration_score + exit_code_score, 2)


def score_runs(runs: List[JobRun], baseline_seconds: float = 0.0) -> List[Dict]:
    """Return a list of dicts with run_id, job_name and score for each run."""
    return [
        {
            "run_id": run.run_id,
            "job_name": run.job_name,
            "score": score_run(run, baseline_seconds=baseline_seconds),
        }
        for run in runs
    ]


def score_by_job(runs: List[JobRun], baseline_seconds: float = 0.0) -> Dict[str, float]:
    """Return a mapping of job_name → average health score across all its runs."""
    totals: Dict[str, List[float]] = {}
    for run in runs:
        s = score_run(run, baseline_seconds=baseline_seconds)
        totals.setdefault(run.job_name, []).append(s)
    return {
        job: round(sum(scores) / len(scores), 2)
        for job, scores in totals.items()
    }
