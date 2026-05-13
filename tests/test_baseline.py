"""Tests for cronlog.baseline."""

from __future__ import annotations

import datetime
import os
import pytest

from cronlog.baseline import (
    compute_baseline,
    exceeds_baseline,
    load_all_baselines,
    load_baseline,
    save_baseline,
    _duration_seconds,
)
from cronlog.models import JobRun, JobStatus


def make_run(job_name: str = "test_job", duration: float = 10.0, finished: bool = True) -> JobRun:
    run = JobRun(job_name=job_name)
    run.started_at = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    if finished:
        run.finished_at = run.started_at + datetime.timedelta(seconds=duration)
        run.status = JobStatus.SUCCESS
        run.exit_code = 0
    return run


def test_duration_seconds_finished_run():
    run = make_run(duration=30.0)
    assert _duration_seconds(run) == pytest.approx(30.0)


def test_duration_seconds_unfinished_run():
    run = make_run(finished=False)
    assert _duration_seconds(run) is None


def test_compute_baseline_empty_list():
    assert compute_baseline([]) is None


def test_compute_baseline_single_run():
    run = make_run(duration=20.0)
    assert compute_baseline([run]) == pytest.approx(20.0)


def test_compute_baseline_averages_durations():
    runs = [make_run(duration=d) for d in [10.0, 20.0, 30.0]]
    assert compute_baseline(runs) == pytest.approx(20.0)


def test_compute_baseline_ignores_unfinished():
    runs = [make_run(duration=10.0), make_run(finished=False)]
    assert compute_baseline(runs) == pytest.approx(10.0)


def test_save_and_load_baseline(tmp_path):
    log_dir = str(tmp_path)
    save_baseline(log_dir, "my_job", 42.5)
    assert load_baseline(log_dir, "my_job") == pytest.approx(42.5)


def test_load_baseline_missing_job(tmp_path):
    assert load_baseline(str(tmp_path), "nonexistent") is None


def test_load_baseline_no_file(tmp_path):
    assert load_baseline(str(tmp_path), "any_job") is None


def test_load_all_baselines_empty(tmp_path):
    assert load_all_baselines(str(tmp_path)) == {}


def test_load_all_baselines_multiple(tmp_path):
    log_dir = str(tmp_path)
    save_baseline(log_dir, "job_a", 5.0)
    save_baseline(log_dir, "job_b", 15.0)
    result = load_all_baselines(log_dir)
    assert result["job_a"] == pytest.approx(5.0)
    assert result["job_b"] == pytest.approx(15.0)


def test_exceeds_baseline_over_threshold():
    run = make_run(duration=13.0)
    assert exceeds_baseline(run, baseline_seconds=10.0, threshold=0.2) is True


def test_exceeds_baseline_within_threshold():
    run = make_run(duration=11.0)
    assert exceeds_baseline(run, baseline_seconds=10.0, threshold=0.2) is False


def test_exceeds_baseline_unfinished_run():
    run = make_run(finished=False)
    assert exceeds_baseline(run, baseline_seconds=10.0) is False
