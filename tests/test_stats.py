import pytest
from datetime import datetime, timezone
from cronlog.models import JobRun, JobStatus
from cronlog.stats import compute_stats, compute_stats_by_job


def make_run(job_name: str, status: JobStatus, duration: float | None = None) -> JobRun:
    run = JobRun(job_name=job_name, command="echo hi")
    run.status = status
    run.duration_seconds = duration
    return run


@pytest.fixture
def mixed_runs():
    return [
        make_run("backup", JobStatus.SUCCESS, 2.5),
        make_run("backup", JobStatus.SUCCESS, 3.0),
        make_run("backup", JobStatus.FAILURE, 1.0),
        make_run("sync", JobStatus.SUCCESS, 5.0),
        make_run("sync", JobStatus.FAILURE, 0.5),
    ]


def test_compute_stats_empty():
    stats = compute_stats([])
    assert stats["total"] == 0
    assert stats["success"] == 0
    assert stats["failure"] == 0
    assert stats["success_rate"] is None
    assert stats["avg_duration_seconds"] is None


def test_compute_stats_total(mixed_runs):
    stats = compute_stats(mixed_runs)
    assert stats["total"] == 5


def test_compute_stats_success_and_failure(mixed_runs):
    stats = compute_stats(mixed_runs)
    assert stats["success"] == 3
    assert stats["failure"] == 2


def test_compute_stats_success_rate(mixed_runs):
    stats = compute_stats(mixed_runs)
    assert stats["success_rate"] == 60.0


def test_compute_stats_avg_duration(mixed_runs):
    stats = compute_stats(mixed_runs)
    expected = round((2.5 + 3.0 + 1.0 + 5.0 + 0.5) / 5, 3)
    assert stats["avg_duration_seconds"] == expected


def test_compute_stats_min_max_duration(mixed_runs):
    stats = compute_stats(mixed_runs)
    assert stats["min_duration_seconds"] == 0.5
    assert stats["max_duration_seconds"] == 5.0


def test_compute_stats_no_durations():
    runs = [make_run("job", JobStatus.SUCCESS, None)]
    stats = compute_stats(runs)
    assert stats["avg_duration_seconds"] is None
    assert stats["min_duration_seconds"] is None
    assert stats["max_duration_seconds"] is None


def test_compute_stats_by_job_keys(mixed_runs):
    breakdown = compute_stats_by_job(mixed_runs)
    assert set(breakdown.keys()) == {"backup", "sync"}


def test_compute_stats_by_job_counts(mixed_runs):
    breakdown = compute_stats_by_job(mixed_runs)
    assert breakdown["backup"]["total"] == 3
    assert breakdown["sync"]["total"] == 2


def test_compute_stats_by_job_success_rate(mixed_runs):
    breakdown = compute_stats_by_job(mixed_runs)
    assert breakdown["backup"]["success_rate"] == round(2 / 3 * 100, 2)
    assert breakdown["sync"]["success_rate"] == 50.0
