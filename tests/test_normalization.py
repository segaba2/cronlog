"""Tests for cronlog.normalization."""

import pytest

from cronlog.normalization import (
    is_valid_job_name,
    normalize_job_name,
    normalize_output,
    normalize_run,
    normalize_runs,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_run(job_name="my_job", stdout="", stderr=""):
    from cronlog.models import JobRun
    run = JobRun(job_name=job_name, command="echo hi")
    run.stdout = stdout
    run.stderr = stderr
    return run


# ---------------------------------------------------------------------------
# normalize_job_name
# ---------------------------------------------------------------------------

def test_normalize_job_name_lowercases():
    assert normalize_job_name("MyJob") == "myjob"


def test_normalize_job_name_strips_whitespace():
    assert normalize_job_name("  my job  ") == "my_job"


def test_normalize_job_name_collapses_spaces_to_underscores():
    assert normalize_job_name("backup  db") == "backup__db"


def test_normalize_job_name_removes_special_chars():
    result = normalize_job_name("job@name!")
    assert "@" not in result
    assert "!" not in result


def test_normalize_job_name_allows_hyphen_dot():
    assert normalize_job_name("my-job.v2") == "my-job.v2"


def test_normalize_job_name_empty_string_returns_empty():
    assert normalize_job_name("") == ""


def test_normalize_job_name_whitespace_only_returns_empty():
    assert normalize_job_name("   ") == ""


# ---------------------------------------------------------------------------
# normalize_output
# ---------------------------------------------------------------------------

def test_normalize_output_strips_trailing_spaces_per_line():
    result = normalize_output("hello   \nworld  ")
    assert result == "hello\nworld"


def test_normalize_output_removes_trailing_blank_lines():
    result = normalize_output("line1\n\n\n")
    assert result == "line1"


def test_normalize_output_none_returns_empty_string():
    assert normalize_output(None) == ""


def test_normalize_output_empty_string_returns_empty():
    assert normalize_output("") == ""


# ---------------------------------------------------------------------------
# normalize_run
# ---------------------------------------------------------------------------

def test_normalize_run_normalizes_job_name():
    run = make_run(job_name="My Job")
    normalize_run(run)
    assert run.job_name == "my_job"


def test_normalize_run_normalizes_stdout():
    run = make_run(stdout="output   \n\n")
    normalize_run(run)
    assert run.stdout == "output"


def test_normalize_run_normalizes_stderr():
    run = make_run(stderr="err   \n")
    normalize_run(run)
    assert run.stderr == "err"


# ---------------------------------------------------------------------------
# normalize_runs
# ---------------------------------------------------------------------------

def test_normalize_runs_processes_all():
    runs = [make_run(job_name="Job A"), make_run(job_name="Job B")]
    result = normalize_runs(runs)
    assert result[0].job_name == "job_a"
    assert result[1].job_name == "job_b"


def test_normalize_runs_empty_list():
    assert normalize_runs([]) == []


# ---------------------------------------------------------------------------
# is_valid_job_name
# ---------------------------------------------------------------------------

def test_is_valid_job_name_true_for_simple_name():
    assert is_valid_job_name("backup_db") is True


def test_is_valid_job_name_false_for_empty():
    assert is_valid_job_name("") is False


def test_is_valid_job_name_false_for_uppercase():
    assert is_valid_job_name("MyJob") is False


def test_is_valid_job_name_false_for_leading_hyphen():
    assert is_valid_job_name("-job") is False
