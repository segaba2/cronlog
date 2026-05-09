"""Tests for cronlog.summary."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.summary import summarise_runs, summarise_by_job, format_summary


def make_run(
    job_name: str = "backup",
    status: JobStatus = JobStatus.SUCCESS,
    duration: float | None = 10.0,
) -> JobRun:
    run = JobRun(job_name=job_name, command="echo hi")
    run.status = status
    if duration is not None:
        run.duration_seconds = duration
        run.finished_at = datetime.now(timezone.utc)
    return run


@pytest.fixture()
def mixed_runs():
    return [
        make_run("backup", JobStatus.SUCCESS, 5.0),
        make_run("backup", JobStatus.FAILURE, 2.0),
        make_run("cleanup", JobStatus.SUCCESS, 8.0),
        make_run("cleanup", JobStatus.TIMEOUT, None),
        make_run("sync", JobStatus.RUNNING, None),
    ]


def test_summarise_runs_empty():
    result = summarise_runs([])
    assert result["total"] == 0
    assert result["success_rate"] is None
    assert result["jobs"] == []


def test_summarise_runs_total(mixed_runs):
    result = summarise_runs(mixed_runs)
    assert result["total"] == 5


def test_summarise_runs_counts(mixed_runs):
    result = summarise_runs(mixed_runs)
    assert result["success"] == 2
    assert result["failure"] == 1
    assert result["timeout"] == 1
    assert result["running"] == 1


def test_summarise_runs_success_rate(mixed_runs):
    result = summarise_runs(mixed_runs)
    # 2 success out of 5 total
    assert result["success_rate"] == 40.0


def test_summarise_runs_avg_duration(mixed_runs):
    result = summarise_runs(mixed_runs)
    # runs with duration: 5.0, 2.0, 8.0 → avg 5.0
    assert result["avg_duration_seconds"] == pytest.approx(5.0)


def test_summarise_runs_jobs_sorted(mixed_runs):
    result = summarise_runs(mixed_runs)
    assert result["jobs"] == ["backup", "cleanup", "sync"]


def test_summarise_by_job_keys(mixed_runs):
    result = summarise_by_job(mixed_runs)
    assert set(result.keys()) == {"backup", "cleanup", "sync"}


def test_summarise_by_job_per_job_counts(mixed_runs):
    result = summarise_by_job(mixed_runs)
    assert result["backup"]["total"] == 2
    assert result["backup"]["success"] == 1
    assert result["backup"]["failure"] == 1
    assert result["cleanup"]["timeout"] == 1


def test_format_summary_contains_total(mixed_runs):
    summary = summarise_runs(mixed_runs)
    output = format_summary(summary)
    assert "5" in output
    assert "Total runs" in output


def test_format_summary_contains_rate(mixed_runs):
    summary = summarise_runs(mixed_runs)
    output = format_summary(summary)
    assert "40.0%" in output


def test_format_summary_empty_shows_na():
    summary = summarise_runs([])
    output = format_summary(summary)
    assert "n/a" in output


def test_format_summary_lists_jobs(mixed_runs):
    summary = summarise_runs(mixed_runs)
    output = format_summary(summary)
    assert "backup" in output
    assert "cleanup" in output
    assert "sync" in output
