"""Tests for cronlog.snapshots."""

from __future__ import annotations

import gzip
import json
import os
from datetime import datetime, timezone, timedelta

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.snapshots import create_snapshot, load_snapshots, delete_snapshot


def _make_run(name: str, status: JobStatus, minutes_ago: int = 5) -> JobRun:
    run = JobRun(job_name=name)
    started = datetime.now(timezone.utc) - timedelta(minutes=minutes_ago)
    run.started_at = started
    run.status = status
    run.exit_code = 0 if status == JobStatus.SUCCESS else 1
    run.stdout = ""
    run.stderr = ""
    run.finished_at = started + timedelta(seconds=10)
    return run


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path)


@pytest.fixture()
def mixed_runs():
    return [
        _make_run("job-a", JobStatus.SUCCESS),
        _make_run("job-a", JobStatus.FAILURE),
        _make_run("job-b", JobStatus.SUCCESS),
    ]


def test_create_snapshot_returns_dict(log_dir, mixed_runs):
    snap = create_snapshot(mixed_runs, log_dir)
    assert isinstance(snap, dict)


def test_create_snapshot_has_summary(log_dir, mixed_runs):
    snap = create_snapshot(mixed_runs, log_dir)
    assert "summary" in snap
    assert snap["summary"]["total"] == 3


def test_create_snapshot_has_by_job(log_dir, mixed_runs):
    snap = create_snapshot(mixed_runs, log_dir)
    assert "by_job" in snap
    assert "job-a" in snap["by_job"]


def test_create_snapshot_uses_label(log_dir, mixed_runs):
    snap = create_snapshot(mixed_runs, log_dir, label="release-1.0")
    assert snap["label"] == "release-1.0"


def test_create_snapshot_persists_file(log_dir, mixed_runs):
    snap = create_snapshot(mixed_runs, log_dir, label="mysnap")
    expected = os.path.join(log_dir, "snapshots", "mysnap.json.gz")
    assert os.path.exists(expected)


def test_persisted_file_is_valid_gzip_json(log_dir, mixed_runs):
    create_snapshot(mixed_runs, log_dir, label="chk")
    path = os.path.join(log_dir, "snapshots", "chk.json.gz")
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["label"] == "chk"


def test_load_snapshots_empty_when_no_dir(log_dir):
    result = load_snapshots(log_dir)
    assert result == []


def test_load_snapshots_returns_all(log_dir, mixed_runs):
    create_snapshot(mixed_runs, log_dir, label="s1")
    create_snapshot(mixed_runs, log_dir, label="s2")
    result = load_snapshots(log_dir)
    assert len(result) == 2


def test_load_snapshots_sorted_by_label(log_dir, mixed_runs):
    create_snapshot(mixed_runs, log_dir, label="b-snap")
    create_snapshot(mixed_runs, log_dir, label="a-snap")
    result = load_snapshots(log_dir)
    assert result[0]["label"] == "a-snap"


def test_delete_snapshot_removes_file(log_dir, mixed_runs):
    create_snapshot(mixed_runs, log_dir, label="to-del")
    removed = delete_snapshot(log_dir, "to-del")
    assert removed is True
    assert load_snapshots(log_dir) == []


def test_delete_snapshot_returns_false_when_missing(log_dir):
    result = delete_snapshot(log_dir, "nonexistent")
    assert result is False
