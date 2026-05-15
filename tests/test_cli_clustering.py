"""Tests for cronlog.cli_clustering."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from cronlog.cli_clustering import add_clustering_subparser, cmd_cluster
from cronlog.models import JobRun, JobStatus


def _make_run(
    job_name: str = "job",
    status: JobStatus = JobStatus.SUCCESS,
    exit_code: int = 0,
    duration: float = 30.0,
) -> JobRun:
    started = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    run = JobRun(job_name=job_name)
    run.started_at = started
    run.finished_at = started + timedelta(seconds=duration)
    run.status = status
    run.exit_code = exit_code
    return run


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "mode": "outcome",
        "bucket_size": 60.0,
        "output_json": False,
        "log_dir": ".cronlog",
        "func": cmd_cluster,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_clustering_subparser_registers_cluster():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_clustering_subparser(subparsers)
    args = parser.parse_args(["cluster"])
    assert args.func == cmd_cluster


def test_cmd_cluster_no_runs_prints_message(capsys, tmp_path):
    args = make_args(log_dir=str(tmp_path))
    cmd_cluster(args)
    captured = capsys.readouterr()
    assert "No runs found" in captured.out


def test_cmd_cluster_outcome_mode_output(capsys, tmp_path, monkeypatch):
    runs = [_make_run(status=JobStatus.SUCCESS), _make_run(status=JobStatus.FAILURE, exit_code=1)]
    mock_storage = MagicMock()
    mock_storage.load_all.return_value = runs
    monkeypatch.setattr("cronlog.cli_clustering.JobRunStorage", lambda _: mock_storage)
    args = make_args(mode="outcome", log_dir=str(tmp_path))
    cmd_cluster(args)
    captured = capsys.readouterr()
    assert "success:0" in captured.out
    assert "failure:1" in captured.out


def test_cmd_cluster_json_output(capsys, tmp_path, monkeypatch):
    runs = [_make_run(), _make_run()]
    mock_storage = MagicMock()
    mock_storage.load_all.return_value = runs
    monkeypatch.setattr("cronlog.cli_clustering.JobRunStorage", lambda _: mock_storage)
    args = make_args(mode="outcome", output_json=True, log_dir=str(tmp_path))
    cmd_cluster(args)
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, dict)
    assert "success:0" in data
    assert data["success:0"] == 2


def test_cmd_cluster_duration_mode(capsys, tmp_path, monkeypatch):
    runs = [_make_run(duration=10.0), _make_run(duration=90.0)]
    mock_storage = MagicMock()
    mock_storage.load_all.return_value = runs
    monkeypatch.setattr("cronlog.cli_clustering.JobRunStorage", lambda _: mock_storage)
    args = make_args(mode="duration", bucket_size=60.0, log_dir=str(tmp_path))
    cmd_cluster(args)
    captured = capsys.readouterr()
    assert "0s-60s" in captured.out
    assert "60s-120s" in captured.out
