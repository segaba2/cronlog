"""Tests for cronlog.fingerprint."""

from __future__ import annotations

import pytest
from datetime import datetime, timezone

from cronlog.models import JobRun, JobStatus
from cronlog.fingerprint import (
    compute_fingerprint,
    fingerprints_match,
    group_by_fingerprint,
    find_matching_runs,
    unique_fingerprints,
)


def make_run(
    job_name: str = "backup",
    exit_code: int = 0,
    stdout: str = "done",
    stderr: str = "",
) -> JobRun:
    run = JobRun(job_name=job_name)
    run.finish(exit_code=exit_code, stdout=stdout, stderr=stderr)
    return run


# ---------------------------------------------------------------------------
# compute_fingerprint
# ---------------------------------------------------------------------------

def test_compute_fingerprint_returns_string():
    run = make_run()
    assert isinstance(compute_fingerprint(run), str)


def test_compute_fingerprint_is_64_hex_chars():
    run = make_run()
    fp = compute_fingerprint(run)
    assert len(fp) == 64
    assert all(c in "0123456789abcdef" for c in fp)


def test_identical_runs_have_same_fingerprint():
    a = make_run(job_name="sync", exit_code=0, stdout="ok", stderr="")
    b = make_run(job_name="sync", exit_code=0, stdout="ok", stderr="")
    assert compute_fingerprint(a) == compute_fingerprint(b)


def test_different_job_name_gives_different_fingerprint():
    a = make_run(job_name="alpha")
    b = make_run(job_name="beta")
    assert compute_fingerprint(a) != compute_fingerprint(b)


def test_different_exit_code_gives_different_fingerprint():
    a = make_run(exit_code=0)
    b = make_run(exit_code=1)
    assert compute_fingerprint(a) != compute_fingerprint(b)


def test_different_stdout_gives_different_fingerprint():
    a = make_run(stdout="hello")
    b = make_run(stdout="world")
    assert compute_fingerprint(a) != compute_fingerprint(b)


def test_stdout_whitespace_is_stripped():
    a = make_run(stdout="done")
    b = make_run(stdout="  done  ")
    assert compute_fingerprint(a) == compute_fingerprint(b)


# ---------------------------------------------------------------------------
# fingerprints_match
# ---------------------------------------------------------------------------

def test_fingerprints_match_true_for_identical():
    a = make_run()
    b = make_run()
    assert fingerprints_match(a, b) is True


def test_fingerprints_match_false_for_different():
    a = make_run(exit_code=0)
    b = make_run(exit_code=2)
    assert fingerprints_match(a, b) is False


# ---------------------------------------------------------------------------
# group_by_fingerprint
# ---------------------------------------------------------------------------

def test_group_by_fingerprint_empty_list():
    assert group_by_fingerprint([]) == {}


def test_group_by_fingerprint_groups_identical_runs():
    a = make_run()
    b = make_run()
    c = make_run(exit_code=1, stdout="err")
    groups = group_by_fingerprint([a, b, c])
    assert len(groups) == 2
    fp_ab = compute_fingerprint(a)
    assert len(groups[fp_ab]) == 2


# ---------------------------------------------------------------------------
# find_matching_runs
# ---------------------------------------------------------------------------

def test_find_matching_runs_empty_pool():
    target = make_run()
    assert find_matching_runs(target, []) == []


def test_find_matching_runs_returns_matches():
    target = make_run(stdout="x")
    match = make_run(stdout="x")
    other = make_run(stdout="y")
    result = find_matching_runs(target, [match, other])
    assert result == [match]


# ---------------------------------------------------------------------------
# unique_fingerprints
# ---------------------------------------------------------------------------

def test_unique_fingerprints_empty_list():
    assert unique_fingerprints([]) == []


def test_unique_fingerprints_deduplicates():
    a = make_run()
    b = make_run()
    c = make_run(exit_code=1)
    fps = unique_fingerprints([a, b, c])
    assert len(fps) == 2


def test_unique_fingerprints_is_sorted():
    runs = [make_run(job_name=n) for n in ["z", "a", "m"]]
    fps = unique_fingerprints(runs)
    assert fps == sorted(fps)
