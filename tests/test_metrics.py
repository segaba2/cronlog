"""Tests for cronlog.metrics."""

from __future__ import annotations

import datetime
from typing import List

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.metrics import compute_runtime_metrics, compute_runtime_metrics_by_job


def make_run(
    job_name: str = "test_job",
    exit_code: int = 0,
    duration: float | None = 5.0,
    status: JobStatus | None = None,
) -> JobRun:
    run = JobRun(job_name=job_name)
    if duration is not None:
        run.finish(exit_code=exit_code, stdout="", stderr="")
        # Override duration directly for test control
        run.duration_seconds = duration
    if status == JobStatus.TIMEOUT:
        run.mark_timeout()
    return run


@pytest.fixture
def mixed_runs() -> List[JobRun]:
    return [
        make_run("job_a", exit_code=0, duration=10.0),
        make_run("job_a", exit_code=1, duration=4.0),
        make_run("job_b", exit_code=0, duration=2.0),
        make_run("job_b", exit_code=0, duration=6.0),
    ]


def test_compute_runtime_metrics_empty():
    result = compute_runtime_metrics([])
    assert result["total"] == 0
    assert result["success_count"] == 0
    assert result["failure_count"] == 0
    assert result["avg_duration_seconds"] is None
    assert result["min_duration_seconds"] is None
    assert result["max_duration_seconds"] is None


def test_compute_runtime_metrics_total(mixed_runs):
    result = compute_runtime_metrics(mixed_runs)
    assert result["total"] == 4


def test_compute_runtime_metrics_success_count(mixed_runs):
    result = compute_runtime_metrics(mixed_runs)
    assert result["success_count"] == 3


def test_compute_runtime_metrics_failure_count(mixed_runs):
    result = compute_runtime_metrics(mixed_runs)
    assert result["failure_count"] == 1


def test_compute_runtime_metrics_avg_duration(mixed_runs):
    result = compute_runtime_metrics(mixed_runs)
    assert result["avg_duration_seconds"] == pytest.approx((10 + 4 + 2 + 6) / 4)


def test_compute_runtime_metrics_min_duration(mixed_runs):
    result = compute_runtime_metrics(mixed_runs)
    assert result["min_duration_seconds"] == pytest.approx(2.0)


def test_compute_runtime_metrics_max_duration(mixed_runs):
    result = compute_runtime_metrics(mixed_runs)
    assert result["max_duration_seconds"] == pytest.approx(10.0)


def test_compute_runtime_metrics_by_job_keys(mixed_runs):
    result = compute_runtime_metrics_by_job(mixed_runs)
    assert set(result.keys()) == {"job_a", "job_b"}


def test_compute_runtime_metrics_by_job_totals(mixed_runs):
    result = compute_runtime_metrics_by_job(mixed_runs)
    assert result["job_a"]["total"] == 2
    assert result["job_b"]["total"] == 2


def test_compute_runtime_metrics_by_job_avg(mixed_runs):
    result = compute_runtime_metrics_by_job(mixed_runs)
    assert result["job_a"]["avg_duration_seconds"] == pytest.approx(7.0)
    assert result["job_b"]["avg_duration_seconds"] == pytest.approx(4.0)


def test_timeout_counted_separately():
    run = JobRun(job_name="timed_out_job")
    run.mark_timeout()
    result = compute_runtime_metrics([run])
    assert result["timeout_count"] == 1
    assert result["success_count"] == 0
    assert result["failure_count"] == 0
