"""Tests for cronlog.scoring."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.scoring import score_by_job, score_run, score_runs


def make_run(
    job_name: str = "test_job",
    status: JobStatus = JobStatus.SUCCESS,
    exit_code: int = 0,
    duration_seconds: float = 10.0,
) -> JobRun:
    started = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    finished = started + timedelta(seconds=duration_seconds)
    run = JobRun(job_name=job_name)
    run.started_at = started
    run.finished_at = finished
    run.status = status
    run.exit_code = exit_code
    return run


# ---------------------------------------------------------------------------
# score_run
# ---------------------------------------------------------------------------

def test_score_run_perfect_success_no_baseline():
    run = make_run(status=JobStatus.SUCCESS, exit_code=0)
    score = score_run(run, baseline_seconds=0.0)
    assert score == 100.0


def test_score_run_failure_returns_low_score():
    run = make_run(status=JobStatus.FAILURE, exit_code=1)
    score = score_run(run, baseline_seconds=0.0)
    assert score == 0.0


def test_score_run_success_with_nonzero_exit_code():
    run = make_run(status=JobStatus.SUCCESS, exit_code=1)
    score = score_run(run, baseline_seconds=0.0)
    # status (50) + duration neutral (30) + exit code (0) = 80
    assert score == 80.0


def test_score_run_within_baseline_full_duration_points():
    run = make_run(status=JobStatus.SUCCESS, exit_code=0, duration_seconds=5.0)
    score = score_run(run, baseline_seconds=10.0)
    # ratio = 0.5 → (1 - (0.5-1)/2) = 1.25 → clamped to 30
    assert score == 100.0


def test_score_run_at_3x_baseline_zero_duration_points():
    run = make_run(status=JobStatus.SUCCESS, exit_code=0, duration_seconds=30.0)
    score = score_run(run, baseline_seconds=10.0)
    # ratio = 3.0 → (1 - (3-1)/2) = 0 → duration_score = 0
    assert score == 70.0


def test_score_run_above_3x_baseline_clamped():
    run = make_run(status=JobStatus.SUCCESS, exit_code=0, duration_seconds=60.0)
    score = score_run(run, baseline_seconds=10.0)
    assert score == 70.0  # duration clamped to 0


def test_score_run_unfinished_run_gets_neutral_duration():
    run = JobRun(job_name="job")
    run.status = JobStatus.SUCCESS
    run.exit_code = 0
    score = score_run(run, baseline_seconds=10.0)
    # duration_seconds returns 0 → ratio = 0 → clamped to 30
    assert score == 100.0


# ---------------------------------------------------------------------------
# score_runs
# ---------------------------------------------------------------------------

def test_score_runs_returns_list_of_dicts():
    runs = [make_run("job_a"), make_run("job_b")]
    result = score_runs(runs)
    assert len(result) == 2
    assert all("run_id" in r and "job_name" in r and "score" in r for r in result)


def test_score_runs_empty_list():
    assert score_runs([]) == []


# ---------------------------------------------------------------------------
# score_by_job
# ---------------------------------------------------------------------------

def test_score_by_job_aggregates_correctly():
    runs = [
        make_run("alpha", status=JobStatus.SUCCESS, exit_code=0),
        make_run("alpha", status=JobStatus.FAILURE, exit_code=1),
    ]
    result = score_by_job(runs)
    assert "alpha" in result
    assert 0.0 < result["alpha"] < 100.0


def test_score_by_job_empty_list():
    assert score_by_job([]) == {}


def test_score_by_job_multiple_jobs():
    runs = [
        make_run("job_a", status=JobStatus.SUCCESS, exit_code=0),
        make_run("job_b", status=JobStatus.FAILURE, exit_code=1),
    ]
    result = score_by_job(runs)
    assert set(result.keys()) == {"job_a", "job_b"}
    assert result["job_a"] > result["job_b"]
