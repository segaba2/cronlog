"""Tests for cronlog.trend module."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from cronlog.trend import duration_trend, failure_rate_trend, run_count_trend


def make_run(job_name: str, status: str, started_at: datetime, duration_seconds: float = 10.0) -> dict:
    finished_at = started_at + timedelta(seconds=duration_seconds)
    return {
        "job_name": job_name,
        "status": status,
        "started_at": started_at.isoformat(),
        "finished_at": finished_at.isoformat(),
        "exit_code": 0 if status == "success" else 1,
    }


DAY1 = datetime(2024, 3, 4, 10, 0, 0, tzinfo=timezone.utc)
DAY2 = datetime(2024, 3, 5, 10, 0, 0, tzinfo=timezone.utc)
DAY3 = datetime(2024, 3, 6, 10, 0, 0, tzinfo=timezone.utc)


@pytest.fixture()
def mixed_runs():
    return [
        make_run("backup", "success", DAY1, 20.0),
        make_run("backup", "failure", DAY1, 5.0),
        make_run("backup", "success", DAY2, 30.0),
        make_run("sync",   "failure", DAY2, 10.0),
        make_run("sync",   "success", DAY3, 15.0),
    ]


# --- duration_trend ---

def test_duration_trend_empty_list():
    assert duration_trend([]) == {}


def test_duration_trend_single_day(mixed_runs):
    result = duration_trend(mixed_runs, bucket="day")
    assert "2024-03-04" in result


def test_duration_trend_averages_within_bucket(mixed_runs):
    result = duration_trend(mixed_runs, bucket="day")
    assert result["2024-03-04"] == pytest.approx(12.5)  # (20+5)/2


def test_duration_trend_multiple_days(mixed_runs):
    result = duration_trend(mixed_runs, bucket="day")
    assert len(result) == 3


def test_duration_trend_week_bucket(mixed_runs):
    result = duration_trend(mixed_runs, bucket="week")
    # All three days fall in the same ISO week 2024-W10
    assert len(result) == 1
    keys = list(result.keys())
    assert keys[0].startswith("2024-W")


def test_duration_trend_skips_unfinished_run():
    run = {"job_name": "x", "status": "running", "started_at": DAY1.isoformat(), "finished_at": None}
    assert duration_trend([run]) == {}


# --- failure_rate_trend ---

def test_failure_rate_trend_empty_list():
    assert failure_rate_trend([]) == {}


def test_failure_rate_trend_all_success():
    runs = [make_run("j", "success", DAY1), make_run("j", "success", DAY1)]
    result = failure_rate_trend(runs)
    assert result["2024-03-04"] == pytest.approx(0.0)


def test_failure_rate_trend_all_failure():
    runs = [make_run("j", "failure", DAY1), make_run("j", "failure", DAY1)]
    result = failure_rate_trend(runs)
    assert result["2024-03-04"] == pytest.approx(1.0)


def test_failure_rate_trend_mixed(mixed_runs):
    result = failure_rate_trend(mixed_runs, bucket="day")
    assert result["2024-03-04"] == pytest.approx(0.5)
    assert result["2024-03-05"] == pytest.approx(0.5)
    assert result["2024-03-06"] == pytest.approx(0.0)


# --- run_count_trend ---

def test_run_count_trend_empty_list():
    assert run_count_trend([]) == {}


def test_run_count_trend_counts_per_day(mixed_runs):
    result = run_count_trend(mixed_runs)
    assert result["2024-03-04"] == 2
    assert result["2024-03-05"] == 2
    assert result["2024-03-06"] == 1


def test_run_count_trend_sorted_keys(mixed_runs):
    result = run_count_trend(mixed_runs)
    assert list(result.keys()) == sorted(result.keys())
