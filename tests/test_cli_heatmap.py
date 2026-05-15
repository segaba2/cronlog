"""Tests for cronlog.cli_heatmap."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronlog.cli_heatmap import add_heatmap_subparser, cmd_heatmap
from cronlog.models import JobRun


def make_args(**kwargs):
    defaults = {
        "mode": "hour",
        "job": None,
        "top": 10,
        "as_json": False,
        "log_dir": ".cronlog",
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def _make_run(job_name: str, started_at: datetime) -> JobRun:
    run = JobRun(job_name=job_name)
    run.started_at = started_at
    return run


_RUNS = [
    _make_run("job-a", datetime(2024, 4, 1, 10, 0, tzinfo=timezone.utc)),
    _make_run("job-a", datetime(2024, 4, 1, 10, 30, tzinfo=timezone.utc)),
    _make_run("job-b", datetime(2024, 4, 2, 12, 0, tzinfo=timezone.utc)),
]


def test_add_heatmap_subparser_registers_heatmap():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_heatmap_subparser(sub)
    args = parser.parse_args(["heatmap"])
    assert hasattr(args, "func")


def test_cmd_heatmap_no_runs_prints_message(capsys):
    with patch("cronlog.cli_heatmap.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = []
        cmd_heatmap(make_args())
    out = capsys.readouterr().out
    assert "No runs" in out


def test_cmd_heatmap_hour_mode_output(capsys):
    with patch("cronlog.cli_heatmap.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = _RUNS
        cmd_heatmap(make_args(mode="hour"))
    out = capsys.readouterr().out
    assert "2024-04-01T10" in out


def test_cmd_heatmap_day_mode_output(capsys):
    with patch("cronlog.cli_heatmap.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = _RUNS
        cmd_heatmap(make_args(mode="day"))
    out = capsys.readouterr().out
    assert "2024-04-01" in out


def test_cmd_heatmap_json_flag(capsys):
    with patch("cronlog.cli_heatmap.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = _RUNS
        cmd_heatmap(make_args(mode="hour", as_json=True))
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert isinstance(parsed, dict)


def test_cmd_heatmap_filters_by_job(capsys):
    with patch("cronlog.cli_heatmap.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = _RUNS
        cmd_heatmap(make_args(mode="hour", job="job-b", as_json=True))
    out = capsys.readouterr().out
    parsed = json.loads(out)
    # Only job-b runs; they fall in hour 12 on 2024-04-02
    assert all("12" in k for k in parsed.keys())
