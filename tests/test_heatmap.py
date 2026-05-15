"""Tests for cronlog.heatmap."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from cronlog.heatmap import (
    format_heatmap,
    heatmap_by_day,
    heatmap_by_hour,
    heatmap_by_weekday_hour,
)
from cronlog.models import JobRun


def make_run(job_name: str, started_at: datetime) -> JobRun:
    run = JobRun(job_name=job_name)
    run.started_at = started_at
    return run


_T1 = datetime(2024, 3, 11, 9, 15, tzinfo=timezone.utc)   # Monday
_T2 = datetime(2024, 3, 11, 9, 45, tzinfo=timezone.utc)   # Monday same hour
_T3 = datetime(2024, 3, 12, 14, 0, tzinfo=timezone.utc)   # Tuesday


@pytest.fixture()
def mixed_runs():
    return [
        make_run("job-a", _T1),
        make_run("job-b", _T2),
        make_run("job-a", _T3),
    ]


def test_heatmap_by_hour_empty_list():
    assert heatmap_by_hour([]) == {}


def test_heatmap_by_hour_groups_same_hour(mixed_runs):
    result = heatmap_by_hour(mixed_runs)
    assert result["2024-03-11T09"] == 2


def test_heatmap_by_hour_different_hours(mixed_runs):
    result = heatmap_by_hour(mixed_runs)
    assert result["2024-03-12T14"] == 1


def test_heatmap_by_day_empty_list():
    assert heatmap_by_day([]) == {}


def test_heatmap_by_day_groups_same_day(mixed_runs):
    result = heatmap_by_day(mixed_runs)
    assert result["2024-03-11"] == 2


def test_heatmap_by_day_different_days(mixed_runs):
    result = heatmap_by_day(mixed_runs)
    assert result["2024-03-12"] == 1


def test_heatmap_by_weekday_hour_empty_list():
    assert heatmap_by_weekday_hour([]) == {}


def test_heatmap_by_weekday_hour_key_is_tuple(mixed_runs):
    result = heatmap_by_weekday_hour(mixed_runs)
    assert (0, 9) in result  # Monday=0, hour=9


def test_heatmap_by_weekday_hour_count(mixed_runs):
    result = heatmap_by_weekday_hour(mixed_runs)
    assert result[(0, 9)] == 2


def test_format_heatmap_empty():
    assert format_heatmap({}) == "No data."


def test_format_heatmap_contains_bucket():
    output = format_heatmap({"2024-03-11T09": 5})
    assert "2024-03-11T09" in output
    assert "5" in output


def test_format_heatmap_respects_top_n():
    data = {f"2024-03-{d:02d}T00": d for d in range(1, 20)}
    output = format_heatmap(data, top_n=3)
    lines = [l for l in output.splitlines() if l.strip() and not l.startswith("-") and "Bucket" not in l]
    assert len(lines) == 3


def test_format_heatmap_sorted_descending():
    data = {"bucket-a": 1, "bucket-b": 10, "bucket-c": 5}
    output = format_heatmap(data, top_n=3)
    lines = [l for l in output.splitlines() if l.strip() and not l.startswith("-") and "Bucket" not in l]
    assert "bucket-b" in lines[0]
