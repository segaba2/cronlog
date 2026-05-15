"""Tests for cronlog.cli_bucketing."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from cronlog.cli_bucketing import add_bucketing_subparser, cmd_bucket
from cronlog.models import JobRun


def _make_run(job_name: str, started_at: datetime) -> JobRun:
    run = JobRun(job_name=job_name)
    run.started_at = started_at
    return run


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "mode": "hour",
        "interval": 5,
        "job": None,
        "json": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


@pytest.fixture()
def storage():
    store = MagicMock()
    store.load_all.return_value = [
        _make_run("alpha", datetime(2024, 6, 15, 10, 0, tzinfo=timezone.utc)),
        _make_run("beta", datetime(2024, 6, 15, 11, 0, tzinfo=timezone.utc)),
        _make_run("alpha", datetime(2024, 6, 16, 9, 0, tzinfo=timezone.utc)),
    ]
    return store


def test_add_bucketing_subparser_registers_bucket():
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers()
    add_bucketing_subparser(subs)
    args = parser.parse_args(["bucket"])
    assert hasattr(args, "func")


def test_cmd_bucket_no_runs_prints_message(capsys):
    store = MagicMock()
    store.load_all.return_value = []
    cmd_bucket(make_args(), store)
    out = capsys.readouterr().out
    assert "No runs found" in out


def test_cmd_bucket_hour_mode_output(capsys, storage):
    cmd_bucket(make_args(mode="hour"), storage)
    out = capsys.readouterr().out
    assert "2024-06-15T10" in out
    assert "2024-06-15T11" in out


def test_cmd_bucket_day_mode_output(capsys, storage):
    cmd_bucket(make_args(mode="day"), storage)
    out = capsys.readouterr().out
    assert "2024-06-15" in out
    assert "2024-06-16" in out


def test_cmd_bucket_json_output(capsys, storage):
    cmd_bucket(make_args(mode="day", json=True), storage)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, dict)
    assert "2024-06-15" in data


def test_cmd_bucket_filters_by_job(capsys, storage):
    cmd_bucket(make_args(mode="day", job="alpha"), storage)
    out = capsys.readouterr().out
    # alpha has runs on both days; beta only on 2024-06-15
    assert "2024-06-15" in out
    assert "2024-06-16" in out


def test_cmd_bucket_interval_mode(capsys):
    store = MagicMock()
    store.load_all.return_value = [
        _make_run("x", datetime(2024, 1, 1, 8, 3, tzinfo=timezone.utc)),
        _make_run("x", datetime(2024, 1, 1, 8, 9, tzinfo=timezone.utc)),
    ]
    cmd_bucket(make_args(mode="interval", interval=5), store)
    out = capsys.readouterr().out
    assert "2024-01-01T08:00" in out
    assert "2024-01-01T08:05" in out
