"""Tests for cronlog.bucketing."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

import pytest

from cronlog.bucketing import (
    bucket_by_day,
    bucket_by_hour,
    bucket_by_minute_interval,
    bucket_run_counts,
    fill_missing_buckets,
)
from cronlog.models import JobRun, JobStatus


def make_run(job_name: str, started_at: datetime) -> JobRun:
    run = JobRun(job_name=job_name)
    run.started_at = started_at
    return run


T = datetime(2024, 6, 15, 10, 23, 0, tzinfo=timezone.utc)
T2 = datetime(2024, 6, 15, 10, 47, 0, tzinfo=timezone.utc)
T3 = datetime(2024, 6, 15, 11, 5, 0, tzinfo=timezone.utc)
T4 = datetime(2024, 6, 16, 9, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def mixed_runs() -> List[JobRun]:
    return [
        make_run("alpha", T),
        make_run("beta", T2),
        make_run("alpha", T3),
        make_run("gamma", T4),
    ]


def test_bucket_by_hour_empty_list():
    assert bucket_by_hour([]) == {}


def test_bucket_by_hour_groups_same_hour(mixed_runs):
    buckets = bucket_by_hour(mixed_runs)
    assert "2024-06-15T10" in buckets
    assert len(buckets["2024-06-15T10"]) == 2


def test_bucket_by_hour_splits_different_hours(mixed_runs):
    buckets = bucket_by_hour(mixed_runs)
    assert "2024-06-15T11" in buckets
    assert len(buckets["2024-06-15T11"]) == 1


def test_bucket_by_hour_keys_are_sorted(mixed_runs):
    keys = list(bucket_by_hour(mixed_runs).keys())
    assert keys == sorted(keys)


def test_bucket_by_day_empty_list():
    assert bucket_by_day([]) == {}


def test_bucket_by_day_groups_same_day(mixed_runs):
    buckets = bucket_by_day(mixed_runs)
    assert "2024-06-15" in buckets
    assert len(buckets["2024-06-15"]) == 3


def test_bucket_by_day_splits_different_days(mixed_runs):
    buckets = bucket_by_day(mixed_runs)
    assert "2024-06-16" in buckets
    assert len(buckets["2024-06-16"]) == 1


def test_bucket_by_minute_interval_invalid_raises():
    with pytest.raises(ValueError):
        bucket_by_minute_interval([], interval_minutes=0)


def test_bucket_by_minute_interval_groups_within_window(mixed_runs):
    # T=10:23 and T2=10:47 should fall in different 30-min buckets
    buckets = bucket_by_minute_interval(mixed_runs, interval_minutes=30)
    assert "2024-06-15T10:00" in buckets
    assert "2024-06-15T10:30" in buckets


def test_bucket_by_minute_interval_same_bucket():
    runs = [
        make_run("x", datetime(2024, 1, 1, 8, 1, tzinfo=timezone.utc)),
        make_run("x", datetime(2024, 1, 1, 8, 4, tzinfo=timezone.utc)),
    ]
    buckets = bucket_by_minute_interval(runs, interval_minutes=5)
    assert len(buckets) == 1
    assert len(list(buckets.values())[0]) == 2


def test_bucket_run_counts(mixed_runs):
    buckets = bucket_by_day(mixed_runs)
    counts = bucket_run_counts(buckets)
    assert counts["2024-06-15"] == 3
    assert counts["2024-06-16"] == 1


def test_fill_missing_buckets_adds_empty_entries():
    start = datetime(2024, 1, 1, 8, 0, tzinfo=timezone.utc)
    end = datetime(2024, 1, 1, 10, 0, tzinfo=timezone.utc)
    filled = fill_missing_buckets({}, start, end, interval_minutes=60)
    assert "2024-01-01T08:00" in filled
    assert "2024-01-01T09:00" in filled
    assert "2024-01-01T10:00" in filled
    assert filled["2024-01-01T08:00"] == []
