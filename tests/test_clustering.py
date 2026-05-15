"""Tests for cronlog.clustering."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import pytest

from cronlog.clustering import (
    cluster_by_duration_bucket,
    cluster_by_job_and_status,
    cluster_by_outcome,
    find_similar_runs,
)
from cronlog.models import JobRun, JobStatus


def make_run(
    job_name: str = "job",
    status: JobStatus = JobStatus.SUCCESS,
    exit_code: int = 0,
    duration: Optional[float] = 30.0,
) -> JobRun:
    started = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    run = JobRun(job_name=job_name)
    run.started_at = started
    run.status = status
    run.exit_code = exit_code
    if duration is not None:
        run.finished_at = started + timedelta(seconds=duration)
    return run


def test_cluster_by_duration_bucket_empty_list():
    assert cluster_by_duration_bucket([]) == {}


def test_cluster_by_duration_bucket_groups_same_bucket():
    runs = [make_run(duration=10.0), make_run(duration=45.0)]
    result = cluster_by_duration_bucket(runs, bucket_size=60.0)
    assert "0s-60s" in result
    assert len(result["0s-60s"]) == 2


def test_cluster_by_duration_bucket_splits_different_buckets():
    runs = [make_run(duration=10.0), make_run(duration=90.0)]
    result = cluster_by_duration_bucket(runs, bucket_size=60.0)
    assert "0s-60s" in result
    assert "60s-120s" in result


def test_cluster_by_duration_bucket_unknown_for_no_finish():
    run = make_run(duration=None)
    result = cluster_by_duration_bucket([run])
    assert "unknown" in result


def test_cluster_by_outcome_empty_list():
    assert cluster_by_outcome([]) == {}


def test_cluster_by_outcome_groups_same_outcome():
    runs = [make_run(status=JobStatus.SUCCESS, exit_code=0)] * 3
    result = cluster_by_outcome(runs)
    assert "success:0" in result
    assert len(result["success:0"]) == 3


def test_cluster_by_outcome_separates_different_exit_codes():
    r1 = make_run(status=JobStatus.FAILURE, exit_code=1)
    r2 = make_run(status=JobStatus.FAILURE, exit_code=2)
    result = cluster_by_outcome([r1, r2])
    assert "failure:1" in result
    assert "failure:2" in result


def test_cluster_by_job_and_status_keys():
    r1 = make_run(job_name="backup", status=JobStatus.SUCCESS)
    r2 = make_run(job_name="backup", status=JobStatus.FAILURE)
    r3 = make_run(job_name="sync", status=JobStatus.SUCCESS)
    result = cluster_by_job_and_status([r1, r2, r3])
    assert "backup:success" in result
    assert "backup:failure" in result
    assert "sync:success" in result


def test_find_similar_runs_empty_list():
    target = make_run(duration=30.0)
    assert find_similar_runs(target, []) == []


def test_find_similar_runs_excludes_self():
    target = make_run(duration=30.0)
    assert find_similar_runs(target, [target]) == []


def test_find_similar_runs_matches_same_status_exit_duration():
    target = make_run(status=JobStatus.SUCCESS, exit_code=0, duration=30.0)
    candidate = make_run(status=JobStatus.SUCCESS, exit_code=0, duration=35.0)
    result = find_similar_runs(target, [candidate], duration_tolerance=10.0)
    assert candidate in result


def test_find_similar_runs_excludes_different_status():
    target = make_run(status=JobStatus.SUCCESS, exit_code=0, duration=30.0)
    candidate = make_run(status=JobStatus.FAILURE, exit_code=0, duration=30.0)
    result = find_similar_runs(target, [candidate])
    assert candidate not in result


def test_find_similar_runs_excludes_outside_tolerance():
    target = make_run(status=JobStatus.SUCCESS, exit_code=0, duration=30.0)
    candidate = make_run(status=JobStatus.SUCCESS, exit_code=0, duration=120.0)
    result = find_similar_runs(target, [candidate], duration_tolerance=10.0)
    assert candidate not in result
