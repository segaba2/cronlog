"""Tests for cronlog.retention pruning helpers."""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

from cronlog.models import JobRun, JobStatus
from cronlog.retention import (
    prune_by_age,
    prune_by_count,
    prune_by_job_count,
    apply_retention,
)


def make_run(job_name: str, days_ago: int = 0) -> JobRun:
    run = JobRun(job_name=job_name, command=f"echo {job_name}")
    run.started_at = datetime.now(timezone.utc) - timedelta(days=days_ago)
    run.status = JobStatus.SUCCESS
    run.exit_code = 0
    run.finished_at = run.started_at + timedelta(seconds=1)
    return run


@pytest.fixture
def mixed_runs():
    return [
        make_run("jobA", days_ago=1),
        make_run("jobA", days_ago=5),
        make_run("jobA", days_ago=10),
        make_run("jobB", days_ago=2),
        make_run("jobB", days_ago=20),
    ]


def test_prune_by_age_keeps_recent(mixed_runs):
    result = prune_by_age(mixed_runs, max_age_days=7)
    assert len(result) == 3
    for r in result:
        assert r.started_at >= datetime.now(timezone.utc) - timedelta(days=7)


def test_prune_by_age_empty_list():
    assert prune_by_age([], max_age_days=30) == []


def test_prune_by_age_removes_all_old():
    result = prune_by_age([make_run("job", days_ago=100)], max_age_days=7)
    assert result == []


def test_prune_by_count_keeps_most_recent(mixed_runs):
    result = prune_by_count(mixed_runs, max_count=2)
    assert len(result) == 2
    sorted_result = sorted(result, key=lambda r: r.started_at, reverse=True)
    assert result == sorted_result


def test_prune_by_count_larger_than_list(mixed_runs):
    result = prune_by_count(mixed_runs, max_count=100)
    assert len(result) == len(mixed_runs)


def test_prune_by_count_zero():
    result = prune_by_count([make_run("job")], max_count=0)
    assert result == []


def test_prune_by_job_count(mixed_runs):
    result = prune_by_job_count(mixed_runs, max_per_job=1)
    job_names = [r.job_name for r in result]
    assert job_names.count("jobA") == 1
    assert job_names.count("jobB") == 1


def test_prune_by_job_count_keeps_newest(mixed_runs):
    result = prune_by_job_count(mixed_runs, max_per_job=1)
    for r in result:
        if r.job_name == "jobA":
            assert r.started_at == max(
                x.started_at for x in mixed_runs if x.job_name == "jobA"
            )


def test_apply_retention_calls_save_all():
    storage = MagicMock()
    storage.load_all.return_value = [make_run("job", days_ago=100)]
    pruned = apply_retention(storage, max_age_days=7)
    assert pruned == 1
    storage.save_all.assert_called_once_with([])


def test_apply_retention_no_policy_keeps_all():
    storage = MagicMock()
    runs = [make_run("job", days_ago=1), make_run("job", days_ago=2)]
    storage.load_all.return_value = runs
    pruned = apply_retention(storage)
    assert pruned == 0
    storage.save_all.assert_called_once_with(runs)
