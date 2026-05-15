"""Tests for cronlog.anomaly."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cronlog.anomaly import (
    compute_mean_stddev,
    detect_duration_anomalies,
    detect_failure_bursts,
    anomaly_report,
)
from cronlog.models import JobRun, JobStatus


def make_run(
    job_name: str = "job",
    status: JobStatus = JobStatus.SUCCESS,
    duration_seconds: float = 10.0,
    offset_hours: int = 0,
) -> JobRun:
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    started = base + timedelta(hours=offset_hours)
    finished = started + timedelta(seconds=duration_seconds)
    run = JobRun(job_name=job_name)
    run.started_at = started
    run.finished_at = finished
    run.status = status
    run.exit_code = 0 if status == JobStatus.SUCCESS else 1
    return run


def test_compute_mean_stddev_empty():
    mean, stddev = compute_mean_stddev([])
    assert mean == 0.0
    assert stddev == 0.0


def test_compute_mean_stddev_single():
    mean, stddev = compute_mean_stddev([5.0])
    assert mean == 5.0
    assert stddev == 0.0


def test_compute_mean_stddev_values():
    mean, stddev = compute_mean_stddev([2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0])
    assert abs(mean - 5.0) < 1e-9
    assert abs(stddev - 2.0) < 1e-9


def test_detect_duration_anomalies_empty_list():
    result = detect_duration_anomalies([])
    assert result == []


def test_detect_duration_anomalies_no_anomaly():
    runs = [make_run(duration_seconds=10.0, offset_hours=i) for i in range(5)]
    result = detect_duration_anomalies(runs, z_threshold=2.0)
    assert result == []


def test_detect_duration_anomalies_finds_outlier():
    normal_runs = [make_run(duration_seconds=10.0, offset_hours=i) for i in range(8)]
    outlier = make_run(duration_seconds=1000.0, offset_hours=10)
    result = detect_duration_anomalies(normal_runs + [outlier], z_threshold=2.0)
    assert outlier in result


def test_detect_duration_anomalies_ignores_unfinished():
    run = JobRun(job_name="job")
    result = detect_duration_anomalies([run])
    assert result == []


def test_detect_failure_bursts_empty_list():
    result = detect_failure_bursts([])
    assert result == []


def test_detect_failure_bursts_no_burst():
    runs = [
        make_run(status=JobStatus.SUCCESS, offset_hours=i) for i in range(5)
    ]
    result = detect_failure_bursts(runs, window=5, min_failures=3)
    assert result == []


def test_detect_failure_bursts_detects_burst():
    runs = [
        make_run(status=JobStatus.FAILURE, offset_hours=i) for i in range(4)
    ] + [make_run(status=JobStatus.SUCCESS, offset_hours=4)]
    result = detect_failure_bursts(runs, window=5, min_failures=3)
    assert len(result) >= 3


def test_anomaly_report_returns_keys():
    runs = [make_run(offset_hours=i) for i in range(5)]
    report = anomaly_report(runs)
    assert "duration_anomalies" in report
    assert "failure_bursts" in report
    assert "total_anomalies" in report


def test_anomaly_report_empty_runs():
    report = anomaly_report([])
    assert report["total_anomalies"] == 0
