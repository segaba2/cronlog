"""Tests for cronlog.archiver."""

from __future__ import annotations

import gzip
import json
import os
from datetime import datetime, timezone

import pytest

from cronlog.archiver import archive_runs, load_archive, list_archives
from cronlog.models import JobRun, JobStatus


def _make_run(job_name: str = "backup", status: JobStatus = JobStatus.SUCCESS) -> JobRun:
    run = JobRun(job_name=job_name)
    run.finish(exit_code=0 if status == JobStatus.SUCCESS else 1, stdout="ok", stderr="")
    return run


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path / "logs")


def test_archive_runs_creates_file(log_dir):
    runs = [_make_run()]
    path = archive_runs(runs, log_dir, label="test")
    assert os.path.isfile(path)
    assert path.endswith(".jsonl.gz")


def test_archive_runs_creates_log_dir_if_missing(tmp_path):
    log_dir = str(tmp_path / "new_dir")
    assert not os.path.exists(log_dir)
    archive_runs([_make_run()], log_dir, label="init")
    assert os.path.isdir(log_dir)


def test_archive_file_is_gzip(log_dir):
    archive_runs([_make_run()], log_dir, label="gz")
    path = list_archives(log_dir)[0]
    with gzip.open(path, "rt") as fh:
        content = fh.read()
    assert len(content) > 0


def test_archive_contains_valid_jsonl(log_dir):
    runs = [_make_run("job_a"), _make_run("job_b")]
    path = archive_runs(runs, log_dir, label="jsonl")
    with gzip.open(path, "rt") as fh:
        lines = [l.strip() for l in fh if l.strip()]
    assert len(lines) == 2
    for line in lines:
        obj = json.loads(line)
        assert "job_name" in obj


def test_load_archive_returns_job_runs(log_dir):
    original = [_make_run("restore"), _make_run("sync", JobStatus.FAILURE)]
    path = archive_runs(original, log_dir, label="load")
    loaded = load_archive(path)
    assert len(loaded) == 2
    assert all(isinstance(r, JobRun) for r in loaded)


def test_load_archive_preserves_job_names(log_dir):
    runs = [_make_run("alpha"), _make_run("beta")]
    path = archive_runs(runs, log_dir, label="names")
    loaded = load_archive(path)
    names = {r.job_name for r in loaded}
    assert names == {"alpha", "beta"}


def test_load_archive_preserves_status(log_dir):
    runs = [_make_run("x", JobStatus.SUCCESS), _make_run("y", JobStatus.FAILURE)]
    path = archive_runs(runs, log_dir, label="status")
    loaded = load_archive(path)
    statuses = {r.job_name: r.status for r in loaded}
    assert statuses["x"] == JobStatus.SUCCESS
    assert statuses["y"] == JobStatus.FAILURE


def test_list_archives_empty_when_no_dir(tmp_path):
    result = list_archives(str(tmp_path / "nonexistent"))
    assert result == []


def test_list_archives_returns_sorted_paths(log_dir):
    archive_runs([_make_run()], log_dir, label="b_second")
    archive_runs([_make_run()], log_dir, label="a_first")
    paths = list_archives(log_dir)
    assert len(paths) == 2
    assert paths == sorted(paths)


def test_archive_empty_list(log_dir):
    path = archive_runs([], log_dir, label="empty")
    loaded = load_archive(path)
    assert loaded == []
