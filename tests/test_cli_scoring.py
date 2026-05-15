"""Tests for cronlog.cli_scoring."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from cronlog.cli_scoring import add_scoring_subparser, cmd_score
from cronlog.models import JobRun, JobStatus


def _make_run(
    job_name: str = "my_job",
    status: JobStatus = JobStatus.SUCCESS,
    exit_code: int = 0,
) -> JobRun:
    started = datetime(2024, 3, 1, 8, 0, 0, tzinfo=timezone.utc)
    run = JobRun(job_name=job_name)
    run.started_at = started
    run.finished_at = started + timedelta(seconds=5)
    run.status = status
    run.exit_code = exit_code
    return run


def make_args(**kwargs) -> SimpleNamespace:
    defaults = {
        "job": None,
        "baseline": 0.0,
        "by_job": False,
        "as_json": False,
        "log_dir": ".cronlog",
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def test_add_scoring_subparser_registers_score():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_scoring_subparser(sub)
    args = parser.parse_args(["score"])
    assert hasattr(args, "func")


def test_cmd_score_no_runs_prints_message(capsys):
    args = make_args()
    with patch("cronlog.cli_scoring.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = []
        cmd_score(args)
    out = capsys.readouterr().out
    assert "No runs found" in out


def test_cmd_score_table_output(capsys):
    runs = [_make_run("backup")]
    args = make_args()
    with patch("cronlog.cli_scoring.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = runs
        cmd_score(args)
    out = capsys.readouterr().out
    assert "backup" in out
    assert "100" in out


def test_cmd_score_json_output(capsys):
    runs = [_make_run("backup")]
    args = make_args(as_json=True)
    with patch("cronlog.cli_scoring.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = runs
        cmd_score(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["job_name"] == "backup"


def test_cmd_score_by_job_output(capsys):
    runs = [_make_run("alpha"), _make_run("beta", status=JobStatus.FAILURE, exit_code=1)]
    args = make_args(by_job=True)
    with patch("cronlog.cli_scoring.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = runs
        cmd_score(args)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" in out


def test_cmd_score_filters_by_job(capsys):
    runs = [_make_run("alpha"), _make_run("beta")]
    args = make_args(job="alpha")
    with patch("cronlog.cli_scoring.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = runs
        cmd_score(args)
    out = capsys.readouterr().out
    assert "alpha" in out
    assert "beta" not in out
