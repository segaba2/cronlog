"""Tests for cronlog.deduplication module."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch
import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.deduplication import (
    deduplicate_by_id,
    deduplicate_by_identity,
    find_duplicates_by_id,
    find_duplicates_by_identity,
    merge_run_lists,
)


DT = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
DT2 = datetime(2024, 1, 15, 11, 0, 0, tzinfo=timezone.utc)


def make_run(job_name: str = "backup", run_id: str = "abc", started_at: datetime = DT) -> JobRun:
    run = JobRun(job_name=job_name)
    run.run_id = run_id
    run.started_at = started_at
    return run


def test_deduplicate_by_id_empty_list():
    assert deduplicate_by_id([]) == []


def test_deduplicate_by_id_no_duplicates():
    runs = [make_run(run_id="a"), make_run(run_id="b"), make_run(run_id="c")]
    result = deduplicate_by_id(runs)
    assert len(result) == 3


def test_deduplicate_by_id_removes_duplicate():
    r1 = make_run(run_id="dup")
    r2 = make_run(run_id="dup")
    r3 = make_run(run_id="unique")
    result = deduplicate_by_id([r1, r2, r3])
    assert len(result) == 2
    assert result[0] is r1
    assert result[1] is r3


def test_deduplicate_by_identity_empty_list():
    assert deduplicate_by_identity([]) == []


def test_deduplicate_by_identity_removes_same_name_and_time():
    r1 = make_run(job_name="sync", run_id="x1", started_at=DT)
    r2 = make_run(job_name="sync", run_id="x2", started_at=DT)
    r3 = make_run(job_name="sync", run_id="x3", started_at=DT2)
    result = deduplicate_by_identity([r1, r2, r3])
    assert len(result) == 2
    assert result[0] is r1
    assert result[1] is r3


def test_deduplicate_by_identity_keeps_different_jobs():
    r1 = make_run(job_name="job_a", run_id="1", started_at=DT)
    r2 = make_run(job_name="job_b", run_id="2", started_at=DT)
    result = deduplicate_by_identity([r1, r2])
    assert len(result) == 2


def test_find_duplicates_by_id_returns_empty_when_unique():
    runs = [make_run(run_id="a"), make_run(run_id="b")]
    assert find_duplicates_by_id(runs) == []


def test_find_duplicates_by_id_returns_second_occurrence():
    r1 = make_run(run_id="dup")
    r2 = make_run(run_id="dup")
    result = find_duplicates_by_id([r1, r2])
    assert result == [r2]


def test_find_duplicates_by_identity_empty_when_unique():
    r1 = make_run(job_name="a", run_id="1", started_at=DT)
    r2 = make_run(job_name="a", run_id="2", started_at=DT2)
    assert find_duplicates_by_identity([r1, r2]) == []


def test_find_duplicates_by_identity_returns_duplicate():
    r1 = make_run(job_name="a", run_id="1", started_at=DT)
    r2 = make_run(job_name="a", run_id="2", started_at=DT)
    result = find_duplicates_by_identity([r1, r2])
    assert result == [r2]


def test_merge_run_lists_combines_and_deduplicates():
    r1 = make_run(run_id="a")
    r2 = make_run(run_id="b")
    r3 = make_run(run_id="a")  # duplicate of r1
    r4 = make_run(run_id="c")
    result = merge_run_lists([r1, r2], [r3, r4])
    assert len(result) == 3
    ids = [r.run_id for r in result]
    assert ids == ["a", "b", "c"]


def test_merge_run_lists_single_list():
    r1 = make_run(run_id="x")
    result = merge_run_lists([r1])
    assert result == [r1]
