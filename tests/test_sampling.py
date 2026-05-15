"""Tests for cronlog.sampling module."""

from __future__ import annotations

import pytest
from unittest.mock import patch
from datetime import datetime, timezone

from cronlog.models import JobRun, JobStatus
from cronlog.sampling import (
    sample_by_rate,
    sample_by_count,
    sample_by_interval,
    sample_by_job,
)


def make_run(job_name: str = "test_job") -> JobRun:
    run = JobRun(job_name=job_name)
    run.finish(exit_code=0, stdout="ok", stderr="")
    return run


@pytest.fixture
def mixed_runs():
    return [
        make_run("job_a"),
        make_run("job_a"),
        make_run("job_b"),
        make_run("job_b"),
        make_run("job_c"),
    ]


# --- sample_by_rate ---

def test_sample_by_rate_full_rate_returns_all(mixed_runs):
    result = sample_by_rate(mixed_runs, 1.0)
    assert len(result) == len(mixed_runs)


def test_sample_by_rate_zero_rate_returns_empty(mixed_runs):
    result = sample_by_rate(mixed_runs, 0.0)
    assert result == []


def test_sample_by_rate_empty_list():
    assert sample_by_rate([], 0.5) == []


def test_sample_by_rate_invalid_raises():
    with pytest.raises(ValueError):
        sample_by_rate([], 1.5)
    with pytest.raises(ValueError):
        sample_by_rate([], -0.1)


def test_sample_by_rate_returns_subset(mixed_runs):
    with patch("cronlog.sampling.random.random", side_effect=[0.1, 0.9, 0.1, 0.9, 0.1]):
        result = sample_by_rate(mixed_runs, 0.5)
    assert len(result) == 3


# --- sample_by_count ---

def test_sample_by_count_returns_n_items(mixed_runs):
    result = sample_by_count(mixed_runs, 3)
    assert len(result) == 3


def test_sample_by_count_more_than_available(mixed_runs):
    result = sample_by_count(mixed_runs, 100)
    assert len(result) == len(mixed_runs)


def test_sample_by_count_zero_returns_empty(mixed_runs):
    result = sample_by_count(mixed_runs, 0)
    assert result == []


def test_sample_by_count_empty_list():
    assert sample_by_count([], 5) == []


def test_sample_by_count_negative_raises():
    with pytest.raises(ValueError):
        sample_by_count([], -1)


# --- sample_by_interval ---

def test_sample_by_interval_every_one_returns_all(mixed_runs):
    result = sample_by_interval(mixed_runs, 1)
    assert result == mixed_runs


def test_sample_by_interval_every_two(mixed_runs):
    result = sample_by_interval(mixed_runs, 2)
    assert result == mixed_runs[::2]
    assert len(result) == 3


def test_sample_by_interval_empty_list():
    assert sample_by_interval([], 2) == []


def test_sample_by_interval_invalid_raises():
    with pytest.raises(ValueError):
        sample_by_interval([], 0)


# --- sample_by_job ---

def test_sample_by_job_full_rate_returns_all(mixed_runs):
    result = sample_by_job(mixed_runs, 1.0)
    assert len(result) == len(mixed_runs)


def test_sample_by_job_zero_rate_returns_empty(mixed_runs):
    result = sample_by_job(mixed_runs, 0.0)
    assert result == []


def test_sample_by_job_empty_list():
    assert sample_by_job([], 0.5) == []


def test_sample_by_job_invalid_rate_raises():
    with pytest.raises(ValueError):
        sample_by_job([], 2.0)
