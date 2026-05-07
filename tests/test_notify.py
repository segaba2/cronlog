"""Tests for cronlog.notify."""

import pytest
from datetime import datetime, timezone, timedelta

from cronlog.models import JobRun, JobStatus
from cronlog import notify as notify_module
from cronlog.notify import (
    register_handler,
    unregister_all,
    notify,
    log_handler,
    failure_only_handler,
)


@pytest.fixture(autouse=True)
def clean_handlers():
    """Ensure handler registry is empty before and after each test."""
    unregister_all()
    yield
    unregister_all()


def _make_run(status: JobStatus, exit_code: int = 0) -> JobRun:
    run = JobRun(job_name="sample-job")
    run.status = status
    run.exit_code = exit_code
    run.stdout = ""
    run.stderr = ""
    run.started_at = datetime.now(timezone.utc)
    run.finished_at = run.started_at + timedelta(seconds=1)
    return run


def test_notify_calls_registered_handler():
    called_with = []
    register_handler(lambda r: called_with.append(r))
    run = _make_run(JobStatus.SUCCESS)
    notify(run)
    assert called_with == [run]


def test_notify_calls_multiple_handlers():
    results = []
    register_handler(lambda r: results.append("h1"))
    register_handler(lambda r: results.append("h2"))
    notify(_make_run(JobStatus.SUCCESS))
    assert results == ["h1", "h2"]


def test_notify_swallows_handler_exceptions():
    def bad_handler(run):
        raise RuntimeError("boom")

    register_handler(bad_handler)
    # Should not raise
    notify(_make_run(JobStatus.SUCCESS))


def test_unregister_all_clears_handlers():
    register_handler(lambda r: None)
    unregister_all()
    results = []
    notify(_make_run(JobStatus.SUCCESS))
    assert results == []


def test_log_handler_prints_success(capsys):
    run = _make_run(JobStatus.SUCCESS, exit_code=0)
    log_handler(run)
    out = capsys.readouterr().out
    assert "SUCCESS" in out
    assert "sample-job" in out


def test_log_handler_prints_failure(capsys):
    run = _make_run(JobStatus.FAILURE, exit_code=1)
    log_handler(run)
    out = capsys.readouterr().out
    assert "FAILURE" in out


def test_failure_only_handler_skips_success():
    called = []
    wrapped = failure_only_handler(lambda r: called.append(r))
    wrapped(_make_run(JobStatus.SUCCESS))
    assert called == []


def test_failure_only_handler_calls_on_failure():
    called = []
    wrapped = failure_only_handler(lambda r: called.append(r))
    run = _make_run(JobStatus.FAILURE, exit_code=1)
    wrapped(run)
    assert called == [run]
