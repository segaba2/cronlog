"""Tests for cronlog.diffing."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.diffing import (
    diff_runs,
    duration_diff_seconds,
    summarise_diff,
    runs_are_equivalent,
)


def make_run(
    job_name: str = "backup",
    exit_code: int = 0,
    status: JobStatus = JobStatus.SUCCESS,
    stdout: str = "",
    stderr: str = "",
    started_at: datetime | None = None,
    finished_at: datetime | None = None,
) -> JobRun:
    run = JobRun(job_name=job_name)
    run.exit_code = exit_code
    run.status = status
    run.stdout = stdout
    run.stderr = stderr
    run.started_at = started_at
    run.finished_at = finished_at
    return run


def _ts(hour: int) -> datetime:
    return datetime(2024, 1, 1, hour, 0, 0, tzinfo=timezone.utc)


# --- diff_runs ---

def test_diff_runs_no_differences():
    a = make_run()
    b = make_run()
    assert diff_runs(a, b) == {}


def test_diff_runs_detects_exit_code_change():
    a = make_run(exit_code=0)
    b = make_run(exit_code=1)
    diffs = diff_runs(a, b)
    assert "exit_code" in diffs
    assert diffs["exit_code"] == {"a": 0, "b": 1}


def test_diff_runs_detects_status_change():
    a = make_run(status=JobStatus.SUCCESS)
    b = make_run(status=JobStatus.FAILURE)
    diffs = diff_runs(a, b)
    assert "status" in diffs


def test_diff_runs_detects_job_name_change():
    a = make_run(job_name="alpha")
    b = make_run(job_name="beta")
    diffs = diff_runs(a, b)
    assert "job_name" in diffs


def test_diff_runs_multiple_fields():
    a = make_run(exit_code=0, stdout="ok")
    b = make_run(exit_code=2, stdout="error")
    diffs = diff_runs(a, b)
    assert "exit_code" in diffs
    assert "stdout" in diffs


# --- duration_diff_seconds ---

def test_duration_diff_seconds_returns_none_if_a_unfinished():
    a = make_run(started_at=_ts(1))
    b = make_run(started_at=_ts(2), finished_at=_ts(3))
    assert duration_diff_seconds(a, b) is None


def test_duration_diff_seconds_returns_none_if_b_unfinished():
    a = make_run(started_at=_ts(1), finished_at=_ts(2))
    b = make_run(started_at=_ts(3))
    assert duration_diff_seconds(a, b) is None


def test_duration_diff_seconds_positive_when_b_slower():
    a = make_run(started_at=_ts(1), finished_at=_ts(2))   # 3600s
    b = make_run(started_at=_ts(1), finished_at=datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc))  # 7200s
    diff = duration_diff_seconds(a, b)
    assert diff == pytest.approx(3600.0)


def test_duration_diff_seconds_negative_when_b_faster():
    a = make_run(started_at=_ts(1), finished_at=datetime(2024, 1, 1, 3, 0, 0, tzinfo=timezone.utc))
    b = make_run(started_at=_ts(1), finished_at=_ts(2))
    diff = duration_diff_seconds(a, b)
    assert diff == pytest.approx(-3600.0)


# --- summarise_diff ---

def test_summarise_diff_contains_run_ids():
    a = make_run()
    b = make_run(exit_code=1)
    summary = summarise_diff(a, b)
    assert summary["run_a"] == a.run_id
    assert summary["run_b"] == b.run_id


def test_summarise_diff_lists_changed_fields():
    a = make_run(exit_code=0)
    b = make_run(exit_code=1)
    summary = summarise_diff(a, b)
    assert "exit_code" in summary["changed_fields"]


def test_summarise_diff_duration_none_when_unfinished():
    a = make_run()
    b = make_run()
    summary = summarise_diff(a, b)
    assert summary["duration_diff_seconds"] is None


# --- runs_are_equivalent ---

def test_runs_are_equivalent_true_for_identical():
    a = make_run()
    b = make_run()
    assert runs_are_equivalent(a, b) is True


def test_runs_are_equivalent_false_when_differ():
    a = make_run(exit_code=0)
    b = make_run(exit_code=1)
    assert runs_are_equivalent(a, b) is False
