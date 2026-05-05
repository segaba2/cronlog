"""Tests for cronlog.models."""

import time
from datetime import datetime

import pytest

from cronlog.models import JobRun, JobStatus


@pytest.fixture
def sample_run() -> JobRun:
    return JobRun(
        job_name="backup",
        command="/usr/bin/backup.sh",
        started_at=datetime.utcnow(),
        tags={"env": "production"},
    )


def test_initial_status_is_running(sample_run):
    assert sample_run.status == JobStatus.RUNNING


def test_run_id_is_generated(sample_run):
    assert sample_run.run_id is not None
    assert len(sample_run.run_id) == 36  # UUID4 format


def test_two_runs_have_unique_ids():
    run1 = JobRun(job_name="j", command="cmd", started_at=datetime.utcnow())
    run2 = JobRun(job_name="j", command="cmd", started_at=datetime.utcnow())
    assert run1.run_id != run2.run_id


def test_finish_sets_success_on_zero_exit(sample_run):
    sample_run.finish(exit_code=0, stdout="done")
    assert sample_run.status == JobStatus.SUCCESS
    assert sample_run.exit_code == 0
    assert sample_run.stdout == "done"


def test_finish_sets_failure_on_nonzero_exit(sample_run):
    sample_run.finish(exit_code=1, stderr="error occurred")
    assert sample_run.status == JobStatus.FAILURE
    assert sample_run.stderr == "error occurred"


def test_finish_computes_duration(sample_run):
    time.sleep(0.05)
    sample_run.finish(exit_code=0)
    assert sample_run.duration_seconds is not None
    assert sample_run.duration_seconds >= 0.05


def test_to_dict_contains_expected_keys(sample_run):
    sample_run.finish(exit_code=0)
    d = sample_run.to_dict()
    for key in ("run_id", "job_name", "command", "status", "started_at",
                "finished_at", "exit_code", "duration_seconds", "stdout",
                "stderr", "tags"):
        assert key in d


def test_to_dict_status_is_string(sample_run):
    sample_run.finish(exit_code=0)
    assert isinstance(sample_run.to_dict()["status"], str)


def test_round_trip_serialization(sample_run):
    sample_run.finish(exit_code=0, stdout="ok", stderr="")
    restored = JobRun.from_dict(sample_run.to_dict())
    assert restored.run_id == sample_run.run_id
    assert restored.job_name == sample_run.job_name
    assert restored.status == JobStatus.SUCCESS
    assert restored.tags == {"env": "production"}
    assert restored.duration_seconds == sample_run.duration_seconds


def test_from_dict_handles_missing_finished_at():
    data = {
        "run_id": "abc-123",
        "job_name": "test",
        "command": "echo hi",
        "started_at": datetime.utcnow().isoformat(),
        "status": "running",
        "finished_at": None,
    }
    run = JobRun.from_dict(data)
    assert run.finished_at is None
    assert run.status == JobStatus.RUNNING
