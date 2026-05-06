"""Tests for cronlog.filters."""

from datetime import datetime, timedelta, timezone

import pytest

from cronlog.filters import (
    apply_filters,
    filter_by_job_name,
    filter_by_status,
    filter_since,
    filter_until,
    latest_per_job,
    sort_by_started_at,
)
from cronlog.models import JobRun, JobStatus


def make_run(job_name: str, exit_code: int = 0, offset_seconds: int = 0) -> JobRun:
    run = JobRun(job_name=job_name, command=f"echo {job_name}")
    run.started_at = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc) + timedelta(
        seconds=offset_seconds
    )
    run.finish(exit_code=exit_code, stdout="", stderr="")
    return run


@pytest.fixture()
def mixed_runs():
    return [
        make_run("backup", exit_code=0, offset_seconds=0),
        make_run("backup", exit_code=1, offset_seconds=60),
        make_run("cleanup", exit_code=0, offset_seconds=120),
        make_run("cleanup", exit_code=0, offset_seconds=180),
        make_run("report", exit_code=1, offset_seconds=240),
    ]


def test_filter_by_status_success(mixed_runs):
    result = filter_by_status(mixed_runs, JobStatus.SUCCESS)
    assert all(r.status == JobStatus.SUCCESS for r in result)
    assert len(result) == 3


def test_filter_by_status_failure(mixed_runs):
    result = filter_by_status(mixed_runs, JobStatus.FAILURE)
    assert len(result) == 2


def test_filter_by_job_name(mixed_runs):
    result = filter_by_job_name(mixed_runs, "backup")
    assert len(result) == 2
    assert all(r.job_name == "backup" for r in result)


def test_filter_by_job_name_case_insensitive(mixed_runs):
    result = filter_by_job_name(mixed_runs, "BACKUP")
    assert len(result) == 2


def test_filter_since(mixed_runs):
    since = datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc)
    result = filter_since(mixed_runs, since)
    assert len(result) == 4


def test_filter_until(mixed_runs):
    until = datetime(2024, 1, 1, 12, 2, 0, tzinfo=timezone.utc)
    result = filter_until(mixed_runs, until)
    assert len(result) == 3


def test_sort_by_started_at_descending(mixed_runs):
    result = sort_by_started_at(mixed_runs, descending=True)
    times = [r.started_at for r in result]
    assert times == sorted(times, reverse=True)


def test_sort_by_started_at_ascending(mixed_runs):
    result = sort_by_started_at(mixed_runs, descending=False)
    times = [r.started_at for r in result]
    assert times == sorted(times)


def test_latest_per_job(mixed_runs):
    result = latest_per_job(mixed_runs)
    job_names = {r.job_name for r in result}
    assert job_names == {"backup", "cleanup", "report"}
    backup_run = next(r for r in result if r.job_name == "backup")
    assert backup_run.status == JobStatus.FAILURE  # the later one failed


def test_apply_filters_combined(mixed_runs):
    since = datetime(2024, 1, 1, 12, 0, 30, tzinfo=timezone.utc)
    result = apply_filters(mixed_runs, job_name="cleanup", since=since)
    assert len(result) == 2
    assert all(r.job_name == "cleanup" for r in result)


def test_apply_filters_no_criteria(mixed_runs):
    result = apply_filters(mixed_runs)
    assert len(result) == len(mixed_runs)
