"""Tests for cronlog.watchdog."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.watchdog import find_overdue_jobs, _last_due_time


def _make_job(name: str, cron: str = "* * * * *") -> MagicMock:
    job = MagicMock()
    job.name = name
    job.cron = cron
    return job


def _make_run(job_name: str, status: str, started_at: datetime) -> JobRun:
    run = JobRun(job_name=job_name)
    run.status = JobStatus(status)
    run.started_at = started_at
    return run


NOW = datetime(2024, 6, 1, 12, 10, 0, tzinfo=timezone.utc)
LAST_DUE = datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)  # 10 min ago


@pytest.fixture()
def storage():
    s = MagicMock()
    s.load_all.return_value = []
    return s


def _patch_last_due(return_value):
    return patch("cronlog.watchdog._last_due_time", return_value=return_value)


def test_no_jobs_returns_empty(storage):
    result = find_overdue_jobs([], storage, grace_seconds=60, now=NOW)
    assert result == []


def test_job_within_grace_not_overdue(storage):
    job = _make_job("backup")
    recent_due = NOW - timedelta(seconds=30)
    with _patch_last_due(recent_due):
        result = find_overdue_jobs([job], storage, grace_seconds=60, now=NOW)
    assert result == []


def test_job_past_grace_with_no_runs_is_overdue(storage):
    job = _make_job("backup")
    with _patch_last_due(LAST_DUE):
        result = find_overdue_jobs([job], storage, grace_seconds=60, now=NOW)
    assert len(result) == 1
    assert result[0]["job_name"] == "backup"


def test_job_with_recent_success_is_not_overdue(storage):
    job = _make_job("backup")
    run = _make_run("backup", "success", LAST_DUE + timedelta(seconds=10))
    storage.load_all.return_value = [run]
    with _patch_last_due(LAST_DUE):
        result = find_overdue_jobs([job], storage, grace_seconds=60, now=NOW)
    assert result == []


def test_job_with_only_failure_is_overdue(storage):
    job = _make_job("backup")
    run = _make_run("backup", "failure", LAST_DUE + timedelta(seconds=5))
    storage.load_all.return_value = [run]
    with _patch_last_due(LAST_DUE):
        result = find_overdue_jobs([job], storage, grace_seconds=60, now=NOW)
    assert len(result) == 1


def test_overdue_entry_contains_expected_keys(storage):
    job = _make_job("nightly", cron="0 2 * * *")
    with _patch_last_due(LAST_DUE):
        result = find_overdue_jobs([job], storage, grace_seconds=60, now=NOW)
    entry = result[0]
    assert "job_name" in entry
    assert "cron" in entry
    assert "last_due" in entry
    assert "grace_seconds" in entry


def test_last_due_returns_none_without_croniter():
    job = _make_job("test", cron="0 * * * *")
    with patch.dict("sys.modules", {"croniter": None}):
        result = _last_due_time(job, NOW)
    assert result is None


def test_no_last_due_skips_job(storage):
    job = _make_job("orphan")
    with _patch_last_due(None):
        result = find_overdue_jobs([job], storage, grace_seconds=60, now=NOW)
    assert result == []
