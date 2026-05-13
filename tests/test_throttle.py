"""Tests for cronlog.throttle."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.throttle import (
    filter_throttled_runs,
    is_throttled,
    last_run_for_job,
)


def make_run(job_name: str, started_offset_seconds: int = 0) -> JobRun:
    run = JobRun(job_name=job_name)
    base = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    run.started_at = base + timedelta(seconds=started_offset_seconds)
    run.status = JobStatus.SUCCESS
    return run


# ---------------------------------------------------------------------------
# last_run_for_job
# ---------------------------------------------------------------------------

def test_last_run_for_job_empty_list():
    assert last_run_for_job([], "backup") is None


def test_last_run_for_job_no_matching_job():
    runs = [make_run("other")]
    assert last_run_for_job(runs, "backup") is None


def test_last_run_for_job_returns_most_recent():
    runs = [make_run("backup", 0), make_run("backup", 60), make_run("backup", 30)]
    result = last_run_for_job(runs, "backup")
    assert result is not None
    assert result.started_at == runs[1].started_at


# ---------------------------------------------------------------------------
# is_throttled
# ---------------------------------------------------------------------------

def test_is_throttled_no_previous_runs():
    assert is_throttled([], "backup", cooldown_seconds=300) is False


def test_is_throttled_run_within_cooldown():
    now = datetime(2024, 1, 1, 12, 5, 0, tzinfo=timezone.utc)
    runs = [make_run("backup", 0)]  # started at 12:00:00
    # 5 minutes ago, cooldown is 10 minutes
    assert is_throttled(runs, "backup", cooldown_seconds=600, now=now) is True


def test_is_throttled_run_outside_cooldown():
    now = datetime(2024, 1, 1, 12, 20, 0, tzinfo=timezone.utc)
    runs = [make_run("backup", 0)]  # started at 12:00:00
    # 20 minutes ago, cooldown is 10 minutes
    assert is_throttled(runs, "backup", cooldown_seconds=600, now=now) is False


def test_is_throttled_zero_cooldown_never_throttles():
    now = datetime(2024, 1, 1, 12, 0, 1, tzinfo=timezone.utc)
    runs = [make_run("backup", 0)]
    assert is_throttled(runs, "backup", cooldown_seconds=0, now=now) is False


def test_is_throttled_ignores_other_jobs():
    now = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)
    runs = [make_run("other_job", 0)]
    assert is_throttled(runs, "backup", cooldown_seconds=600, now=now) is False


# ---------------------------------------------------------------------------
# filter_throttled_runs
# ---------------------------------------------------------------------------

def test_filter_throttled_runs_empty_list():
    assert filter_throttled_runs([], cooldown_seconds=60) == []


def test_filter_throttled_runs_zero_cooldown_keeps_all():
    runs = [make_run("backup", 0), make_run("backup", 10)]
    result = filter_throttled_runs(runs, cooldown_seconds=0)
    assert len(result) == 2


def test_filter_throttled_runs_collapses_close_runs():
    # Two runs 30 seconds apart, cooldown = 60 s  -> keep only the later one
    runs = [make_run("backup", 0), make_run("backup", 30)]
    result = filter_throttled_runs(runs, cooldown_seconds=60)
    assert len(result) == 1
    assert result[0].started_at == runs[1].started_at


def test_filter_throttled_runs_keeps_separated_runs():
    # Two runs 120 seconds apart, cooldown = 60 s -> keep both
    runs = [make_run("backup", 0), make_run("backup", 120)]
    result = filter_throttled_runs(runs, cooldown_seconds=60)
    assert len(result) == 2


def test_filter_throttled_runs_handles_multiple_jobs_independently():
    runs = [
        make_run("backup", 0),
        make_run("backup", 30),   # within cooldown of first backup
        make_run("deploy", 0),
        make_run("deploy", 30),   # within cooldown of first deploy
    ]
    result = filter_throttled_runs(runs, cooldown_seconds=60)
    # Each job should be collapsed to 1 run
    assert len(result) == 2
    job_names = {r.job_name for r in result}
    assert job_names == {"backup", "deploy"}
