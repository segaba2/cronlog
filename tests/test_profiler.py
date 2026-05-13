"""Tests for cronlog.profiler."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.profiler import (
    compute_average_duration,
    find_slow_runs,
    profile_by_job,
    slowest_runs,
    _duration_seconds,
)


def make_run(job_name: str, duration: float | None, status: JobStatus = JobStatus.SUCCESS) -> JobRun:
    run = JobRun(job_name=job_name)
    run.status = status
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    run.started_at = base
    if duration is not None:
        run.finished_at = base + timedelta(seconds=duration)
    return run


@pytest.fixture
def mixed_runs():
    return [
        make_run("backup", 30.0),
        make_run("backup", 90.0),
        make_run("cleanup", 120.0),
        make_run("cleanup", 10.0),
        make_run("report", None),  # still running
    ]


def test_duration_seconds_finished_run():
    run = make_run("job", 45.0)
    assert _duration_seconds(run) == pytest.approx(45.0)


def test_duration_seconds_unfinished_run():
    run = make_run("job", None)
    assert _duration_seconds(run) is None


def test_compute_average_duration_empty():
    assert compute_average_duration([]) is None


def test_compute_average_duration_skips_unfinished(mixed_runs):
    avg = compute_average_duration(mixed_runs)
    # (30 + 90 + 120 + 10) / 4 == 62.5
    assert avg == pytest.approx(62.5)


def test_compute_average_duration_all_unfinished():
    runs = [make_run("job", None), make_run("job", None)]
    assert compute_average_duration(runs) is None


def test_find_slow_runs_returns_only_exceeding(mixed_runs):
    slow = find_slow_runs(mixed_runs, threshold_seconds=80.0)
    names_durations = [(_duration_seconds(r)) for r in slow]
    assert all(d > 80.0 for d in names_durations)
    assert len(slow) == 2


def test_find_slow_runs_empty_list():
    assert find_slow_runs([], threshold_seconds=10.0) == []


def test_find_slow_runs_none_exceed():
    runs = [make_run("job", 5.0), make_run("job", 3.0)]
    assert find_slow_runs(runs, threshold_seconds=10.0) == []


def test_profile_by_job_empty():
    assert profile_by_job([]) == {}


def test_profile_by_job_keys(mixed_runs):
    stats = profile_by_job(mixed_runs)
    assert set(stats.keys()) == {"backup", "cleanup"}


def test_profile_by_job_counts(mixed_runs):
    stats = profile_by_job(mixed_runs)
    assert stats["backup"]["count"] == 2
    assert stats["cleanup"]["count"] == 2


def test_profile_by_job_avg(mixed_runs):
    stats = profile_by_job(mixed_runs)
    assert stats["backup"]["avg_seconds"] == pytest.approx(60.0)


def test_profile_by_job_min_max(mixed_runs):
    stats = profile_by_job(mixed_runs)
    assert stats["cleanup"]["min_seconds"] == pytest.approx(10.0)
    assert stats["cleanup"]["max_seconds"] == pytest.approx(120.0)


def test_slowest_runs_returns_n(mixed_runs):
    top = slowest_runs(mixed_runs, n=2)
    assert len(top) == 2


def test_slowest_runs_ordered(mixed_runs):
    top = slowest_runs(mixed_runs, n=3)
    durations = [_duration_seconds(r) for r in top]
    assert durations == sorted(durations, reverse=True)


def test_slowest_runs_empty_list():
    assert slowest_runs([], n=5) == []
