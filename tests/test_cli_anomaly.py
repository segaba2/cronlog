"""Tests for cronlog.cli_anomaly."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronlog.cli_anomaly import add_anomaly_subparser, cmd_anomaly
from cronlog.models import JobRun, JobStatus


def _make_run(
    job_name: str = "job",
    status: JobStatus = JobStatus.SUCCESS,
    duration: float = 10.0,
    offset: int = 0,
) -> JobRun:
    base = datetime(2024, 3, 1, 10, 0, 0, tzinfo=timezone.utc)
    run = JobRun(job_name=job_name)
    run.started_at = base + timedelta(hours=offset)
    run.finished_at = run.started_at + timedelta(seconds=duration)
    run.status = status
    run.exit_code = 0 if status == JobStatus.SUCCESS else 1
    return run


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "log_dir": "logs",
        "mode": "all",
        "z_threshold": 2.0,
        "job": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_anomaly_subparser_registers_command():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_anomaly_subparser(subparsers)
    args = parser.parse_args(["anomaly"])
    assert hasattr(args, "func")


def test_cmd_anomaly_no_runs_prints_message(capsys):
    args = make_args()
    with patch("cronlog.cli_anomaly.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = []
        cmd_anomaly(args)
    out = capsys.readouterr().out
    assert "No runs found" in out


def test_cmd_anomaly_duration_mode(capsys):
    runs = [_make_run(duration=10.0, offset=i) for i in range(8)]
    runs.append(_make_run(duration=9999.0, offset=10))
    args = make_args(mode="duration", z_threshold=2.0)
    with patch("cronlog.cli_anomaly.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = runs
        cmd_anomaly(args)
    out = capsys.readouterr().out
    assert "Duration Anomalies" in out


def test_cmd_anomaly_bursts_mode(capsys):
    runs = [_make_run(status=JobStatus.FAILURE, offset=i) for i in range(4)]
    args = make_args(mode="bursts")
    with patch("cronlog.cli_anomaly.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = runs
        cmd_anomaly(args)
    out = capsys.readouterr().out
    assert "Failure Bursts" in out


def test_cmd_anomaly_filters_by_job(capsys):
    runs = [
        _make_run(job_name="alpha", offset=i) for i in range(3)
    ] + [
        _make_run(job_name="beta", offset=i) for i in range(3)
    ]
    args = make_args(mode="all", job="alpha")
    with patch("cronlog.cli_anomaly.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = runs
        cmd_anomaly(args)
    out = capsys.readouterr().out
    assert "beta" not in out
