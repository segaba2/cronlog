"""Tests for cronlog.grouping."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.grouping import (
    group_by_job_name,
    group_by_status,
    group_by_date,
    group_by_hour,
    group_by_exit_code,
    summarise_groups,
)


def make_run(
    job_name: str,
    status: JobStatus = JobStatus.SUCCESS,
    exit_code: int = 0,
    started_at: datetime | None = None,
) -> JobRun:
    run = JobRun(job_name=job_name)
    run.started_at = started_at or datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    run.status = status
    run.exit_code = exit_code
    run.finished_at = run.started_at
    return run


@pytest.fixture()
def mixed_runs() -> List[JobRun]:
    return [
        make_run("backup", JobStatus.SUCCESS, 0, datetime(2024, 6, 1, 8, 0, tzinfo=timezone.utc)),
        make_run("backup", JobStatus.FAILURE, 1, datetime(2024, 6, 2, 8, 0, tzinfo=timezone.utc)),
        make_run("cleanup", JobStatus.SUCCESS, 0, datetime(2024, 6, 1, 9, 0, tzinfo=timezone.utc)),
        make_run("cleanup", JobStatus.FAILURE, 2, datetime(2024, 6, 1, 10, 0, tzinfo=timezone.utc)),
        make_run("report", JobStatus.SUCCESS, 0, datetime(2024, 6, 3, 8, 0, tzinfo=timezone.utc)),
    ]


def test_group_by_job_name_keys(mixed_runs):
    groups = group_by_job_name(mixed_runs)
    assert set(groups.keys()) == {"backup", "cleanup", "report"}


def test_group_by_job_name_counts(mixed_runs):
    groups = group_by_job_name(mixed_runs)
    assert len(groups["backup"]) == 2
    assert len(groups["cleanup"]) == 2
    assert len(groups["report"]) == 1


def test_group_by_job_name_empty_list():
    assert group_by_job_name([]) == {}


def test_group_by_status_keys(mixed_runs):
    groups = group_by_status(mixed_runs)
    assert "success" in groups
    assert "failure" in groups


def test_group_by_status_counts(mixed_runs):
    groups = group_by_status(mixed_runs)
    assert len(groups["success"]) == 3
    assert len(groups["failure"]) == 2


def test_group_by_date_keys(mixed_runs):
    groups = group_by_date(mixed_runs)
    assert "2024-06-01" in groups
    assert "2024-06-02" in groups
    assert "2024-06-03" in groups


def test_group_by_date_counts(mixed_runs):
    groups = group_by_date(mixed_runs)
    assert len(groups["2024-06-01"]) == 3
    assert len(groups["2024-06-02"]) == 1


def test_group_by_hour(mixed_runs):
    groups = group_by_hour(mixed_runs)
    assert "2024-06-01 08" in groups
    assert "2024-06-01 09" in groups


def test_group_by_exit_code(mixed_runs):
    groups = group_by_exit_code(mixed_runs)
    assert 0 in groups
    assert len(groups[0]) == 3
    assert 1 in groups
    assert 2 in groups


def test_summarise_groups(mixed_runs):
    groups = group_by_job_name(mixed_runs)
    summary = summarise_groups(groups)
    assert summary["backup"]["total"] == 2
    assert summary["backup"]["success"] == 1
    assert summary["backup"]["failure"] == 1
    assert summary["report"]["total"] == 1
    assert summary["report"]["failure"] == 0


def test_summarise_groups_empty():
    assert summarise_groups({}) == {}
