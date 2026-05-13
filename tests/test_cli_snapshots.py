"""Tests for cronlog.cli_snapshots."""

from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from cronlog.cli_snapshots import add_snapshots_subparser, cmd_snapshot
from cronlog.snapshots import create_snapshot
from cronlog.models import JobRun, JobStatus
from datetime import datetime, timezone, timedelta


def _make_run(name: str, status: JobStatus) -> JobRun:
    run = JobRun(job_name=name)
    run.started_at = datetime.now(timezone.utc) - timedelta(minutes=2)
    run.status = status
    run.exit_code = 0 if status == JobStatus.SUCCESS else 1
    run.stdout = run.stderr = ""
    run.finished_at = run.started_at + timedelta(seconds=5)
    return run


def make_args(**kwargs):
    defaults = {"snapshot_cmd": "create", "log_dir": ".cronlog", "label": "", "as_json": False}
    defaults.update(kwargs)
    ns = argparse.Namespace(**defaults)
    ns.func = cmd_snapshot
    return ns


def test_add_snapshots_subparser_registers_snapshot():
    parser = argparse.ArgumentParser()
    sp = parser.add_subparsers(dest="cmd")
    add_snapshots_subparser(sp)
    args = parser.parse_args(["snapshot", "list"])
    assert args.snapshot_cmd == "list"


def test_cmd_create_prints_label(tmp_path, capsys):
    runs = [_make_run("j", JobStatus.SUCCESS)]
    with patch("cronlog.cli_snapshots.JobRunStorage") as MockStorage:
        MockStorage.return_value.load_all.return_value = runs
        args = make_args(snapshot_cmd="create", log_dir=str(tmp_path), label="v1")
        cmd_snapshot(args)
    out = capsys.readouterr().out
    assert "v1" in out


def test_cmd_list_empty_prints_message(tmp_path, capsys):
    args = make_args(snapshot_cmd="list", log_dir=str(tmp_path))
    cmd_snapshot(args)
    out = capsys.readouterr().out
    assert "No snapshots" in out


def test_cmd_list_shows_snapshots(tmp_path, capsys):
    runs = [_make_run("j", JobStatus.SUCCESS)]
    create_snapshot(runs, str(tmp_path), label="snap-abc")
    args = make_args(snapshot_cmd="list", log_dir=str(tmp_path))
    cmd_snapshot(args)
    out = capsys.readouterr().out
    assert "snap-abc" in out


def test_cmd_list_json_flag(tmp_path, capsys):
    runs = [_make_run("j", JobStatus.SUCCESS)]
    create_snapshot(runs, str(tmp_path), label="jsnap")
    args = make_args(snapshot_cmd="list", log_dir=str(tmp_path), as_json=True)
    cmd_snapshot(args)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert isinstance(data, list)
    assert data[0]["label"] == "jsnap"


def test_cmd_delete_existing(tmp_path, capsys):
    runs = [_make_run("j", JobStatus.SUCCESS)]
    create_snapshot(runs, str(tmp_path), label="del-me")
    args = make_args(snapshot_cmd="delete", log_dir=str(tmp_path), label="del-me")
    cmd_snapshot(args)
    out = capsys.readouterr().out
    assert "Deleted" in out


def test_cmd_delete_missing_exits(tmp_path):
    args = make_args(snapshot_cmd="delete", log_dir=str(tmp_path), label="ghost")
    with pytest.raises(SystemExit) as exc:
        cmd_snapshot(args)
    assert exc.value.code == 1
