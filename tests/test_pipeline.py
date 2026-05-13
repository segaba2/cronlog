"""Tests for cronlog.pipeline."""

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog import pipeline as pl


@pytest.fixture(autouse=True)
def clean_pipelines():
    pl.unregister_all()
    yield
    pl.unregister_all()


def _make_run(job_name: str, status: JobStatus = JobStatus.SUCCESS) -> JobRun:
    run = JobRun(job_name=job_name)
    if status == JobStatus.SUCCESS:
        run.finish(exit_code=0, stdout="", stderr="")
    elif status == JobStatus.FAILURE:
        run.finish(exit_code=1, stdout="", stderr="err")
    return run


def test_create_pipeline_returns_id():
    pid = pl.create_pipeline()
    assert isinstance(pid, str)
    assert len(pid) > 0


def test_create_pipeline_with_explicit_id():
    pid = pl.create_pipeline("my-pipeline")
    assert pid == "my-pipeline"


def test_create_pipeline_is_idempotent():
    pid1 = pl.create_pipeline("p1")
    pid2 = pl.create_pipeline("p1")
    assert pid1 == pid2
    assert pl.get_pipeline_run_ids("p1") == []


def test_add_run_to_pipeline_records_run_id():
    run = _make_run("job-a")
    pl.add_run_to_pipeline("p1", run)
    assert run.run_id in pl.get_pipeline_run_ids("p1")


def test_add_run_to_pipeline_sets_metadata():
    run = _make_run("job-a")
    pl.add_run_to_pipeline("p1", run)
    assert run.metadata.get("pipeline_id") == "p1"


def test_add_run_is_idempotent():
    run = _make_run("job-a")
    pl.add_run_to_pipeline("p1", run)
    pl.add_run_to_pipeline("p1", run)
    assert pl.get_pipeline_run_ids("p1").count(run.run_id) == 1


def test_get_pipeline_runs_returns_correct_runs():
    r1 = _make_run("job-a")
    r2 = _make_run("job-b")
    r3 = _make_run("job-c")
    pl.add_run_to_pipeline("p1", r1)
    pl.add_run_to_pipeline("p1", r2)
    result = pl.get_pipeline_runs("p1", [r1, r2, r3])
    assert result == [r1, r2]


def test_pipeline_status_all_success():
    r1 = _make_run("job-a", JobStatus.SUCCESS)
    r2 = _make_run("job-b", JobStatus.SUCCESS)
    pl.add_run_to_pipeline("p1", r1)
    pl.add_run_to_pipeline("p1", r2)
    assert pl.pipeline_status("p1", [r1, r2]) == JobStatus.SUCCESS


def test_pipeline_status_one_failure():
    r1 = _make_run("job-a", JobStatus.SUCCESS)
    r2 = _make_run("job-b", JobStatus.FAILURE)
    pl.add_run_to_pipeline("p1", r1)
    pl.add_run_to_pipeline("p1", r2)
    assert pl.pipeline_status("p1", [r1, r2]) == JobStatus.FAILURE


def test_pipeline_status_running_if_any_running():
    r1 = _make_run("job-a", JobStatus.SUCCESS)
    r2 = JobRun(job_name="job-b")  # still RUNNING
    pl.add_run_to_pipeline("p1", r1)
    pl.add_run_to_pipeline("p1", r2)
    assert pl.pipeline_status("p1", [r1, r2]) == JobStatus.RUNNING


def test_pipeline_status_empty_pipeline_is_running():
    pl.create_pipeline("empty")
    assert pl.pipeline_status("empty", []) == JobStatus.RUNNING


def test_all_pipeline_ids():
    pl.create_pipeline("alpha")
    pl.create_pipeline("beta")
    ids = pl.all_pipeline_ids()
    assert "alpha" in ids
    assert "beta" in ids
