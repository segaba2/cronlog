"""Tests for cronlog.storage.JobRunStorage."""

import pytest
from pathlib import Path

from cronlog.models import JobRun, JobStatus
from cronlog.storage import JobRunStorage


@pytest.fixture()
def storage(tmp_path: Path) -> JobRunStorage:
    return JobRunStorage(log_dir=tmp_path)


@pytest.fixture()
def finished_run() -> JobRun:
    run = JobRun(job_name="backup", command="tar -czf /tmp/backup.tar.gz /data")
    run.finish(exit_code=0, output="Done.")
    return run


def test_save_creates_log_file(storage: JobRunStorage, finished_run: JobRun):
    storage.save(finished_run)
    assert storage.log_file.exists()


def test_load_all_returns_empty_when_no_file(storage: JobRunStorage):
    assert storage.load_all() == []


def test_save_and_load_roundtrip(storage: JobRunStorage, finished_run: JobRun):
    storage.save(finished_run)
    runs = storage.load_all()
    assert len(runs) == 1
    loaded = runs[0]
    assert loaded.run_id == finished_run.run_id
    assert loaded.job_name == finished_run.job_name
    assert loaded.status == JobStatus.SUCCESS
    assert loaded.output == "Done."


def test_multiple_runs_persisted(storage: JobRunStorage):
    for i in range(3):
        run = JobRun(job_name="task", command=f"echo {i}")
        run.finish(exit_code=0, output=str(i))
        storage.save(run)
    assert len(storage.load_all()) == 3


def test_find_by_job_name(storage: JobRunStorage):
    for name in ("alpha", "beta", "alpha"):
        run = JobRun(job_name=name, command="true")
        run.finish(exit_code=0, output="")
        storage.save(run)
    results = storage.find_by_job_name("alpha")
    assert len(results) == 2
    assert all(r.job_name == "alpha" for r in results)


def test_find_by_run_id(storage: JobRunStorage, finished_run: JobRun):
    storage.save(finished_run)
    found = storage.find_by_run_id(finished_run.run_id)
    assert found is not None
    assert found.run_id == finished_run.run_id


def test_find_by_run_id_missing(storage: JobRunStorage):
    assert storage.find_by_run_id("nonexistent-id") is None


def test_clear_removes_all_records(storage: JobRunStorage, finished_run: JobRun):
    storage.save(finished_run)
    storage.clear()
    assert storage.load_all() == []
    assert not storage.log_file.exists()
