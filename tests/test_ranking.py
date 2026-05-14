"""Tests for cronlog.ranking."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.ranking import (
    rank_by_duration,
    rank_by_failure_rate,
    rank_by_run_count,
    top_n,
)


def make_run(
    job_name: str,
    status: JobStatus = JobStatus.SUCCESS,
    duration_seconds: float | None = 10.0,
) -> JobRun:
    now = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    run = JobRun(job_name=job_name)
    run.started_at = now
    if duration_seconds is not None:
        run.finished_at = now + timedelta(seconds=duration_seconds)
    run.status = status
    run.exit_code = 0 if status == JobStatus.SUCCESS else 1
    return run


@pytest.fixture
def mixed_runs():
    return [
        make_run("job_a", JobStatus.SUCCESS, 30.0),
        make_run("job_a", JobStatus.FAILURE, 5.0),
        make_run("job_b", JobStatus.SUCCESS, 60.0),
        make_run("job_b", JobStatus.FAILURE, 20.0),
        make_run("job_c", JobStatus.SUCCESS, 10.0),
    ]


# --- rank_by_duration ---

def test_rank_by_duration_empty_list():
    assert rank_by_duration([]) == []


def test_rank_by_duration_descending(mixed_runs):
    ranked = rank_by_duration(mixed_runs)
    durations = [r.finished_at - r.started_at for _, r in ranked]
    assert durations == sorted(durations, reverse=True)


def test_rank_by_duration_ascending(mixed_runs):
    ranked = rank_by_duration(mixed_runs, descending=False)
    durations = [r.finished_at - r.started_at for _, r in ranked]
    assert durations == sorted(durations)


def test_rank_by_duration_ranks_start_at_one(mixed_runs):
    ranked = rank_by_duration(mixed_runs)
    assert ranked[0][0] == 1


def test_rank_by_duration_excludes_unfinished_runs():
    runs = [make_run("job_a", duration_seconds=None), make_run("job_b", duration_seconds=5.0)]
    ranked = rank_by_duration(runs)
    assert len(ranked) == 1
    assert ranked[0][1].job_name == "job_b"


# --- rank_by_failure_rate ---

def test_rank_by_failure_rate_empty_list():
    assert rank_by_failure_rate([]) == []


def test_rank_by_failure_rate_highest_first(mixed_runs):
    ranked = rank_by_failure_rate(mixed_runs)
    rates = [r for _, r, _ in ranked]
    assert rates == sorted(rates, reverse=True)


def test_rank_by_failure_rate_all_success():
    runs = [make_run("job_a", JobStatus.SUCCESS) for _ in range(3)]
    ranked = rank_by_failure_rate(runs)
    assert ranked[0][1] == 0.0


def test_rank_by_failure_rate_includes_total_count(mixed_runs):
    ranked = rank_by_failure_rate(mixed_runs)
    totals = {name: total for name, _, total in ranked}
    assert totals["job_a"] == 2
    assert totals["job_b"] == 2
    assert totals["job_c"] == 1


# --- rank_by_run_count ---

def test_rank_by_run_count_empty_list():
    assert rank_by_run_count([]) == []


def test_rank_by_run_count_most_frequent_first(mixed_runs):
    ranked = rank_by_run_count(mixed_runs)
    counts = [c for _, c in ranked]
    assert counts == sorted(counts, reverse=True)


def test_rank_by_run_count_correct_values(mixed_runs):
    ranked = rank_by_run_count(mixed_runs)
    count_map = dict(ranked)
    assert count_map["job_a"] == 2
    assert count_map["job_b"] == 2
    assert count_map["job_c"] == 1


# --- top_n ---

def test_top_n_returns_first_n_items():
    items = [(1, "a"), (2, "b"), (3, "c"), (4, "d")]
    assert top_n(items, 2) == [(1, "a"), (2, "b")]


def test_top_n_larger_than_list():
    items = [(1, "a"), (2, "b")]
    assert top_n(items, 10) == items


def test_top_n_zero_returns_empty():
    items = [(1, "a"), (2, "b")]
    assert top_n(items, 0) == []
