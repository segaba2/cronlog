"""Tests for cronlog.cli_schedule."""

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cronlog.cli_schedule import add_schedule_subparser, cmd_schedule
from cronlog.schedule import ScheduledJob, ScheduleStore


def make_args(**kwargs):
    defaults = dict(
        schedule_cmd="list",
        schedules_file="schedules.json",
        func=cmd_schedule,
    )
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_schedule_subparser_registers_schedule():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_schedule_subparser(sub)
    args = parser.parse_args(["schedule", "list"])
    assert args.cmd == "schedule"


def test_cmd_list_empty(tmp_path, capsys):
    args = make_args(schedule_cmd="list", schedules_file=str(tmp_path / "s.json"))
    cmd_schedule(args)
    out = capsys.readouterr().out
    assert "No scheduled jobs" in out


def test_cmd_add_creates_job(tmp_path, capsys):
    sf = str(tmp_path / "s.json")
    args = make_args(
        schedule_cmd="add",
        schedules_file=sf,
        name="myjob",
        command="echo hello",
        cron_expr="* * * * *",
        tags=[],
        description="",
    )
    cmd_schedule(args)
    out = capsys.readouterr().out
    assert "added" in out
    store = ScheduleStore(path=sf)
    assert store.get("myjob") is not None


def test_cmd_add_duplicate_prints_error(tmp_path, capsys):
    sf = str(tmp_path / "s.json")
    store = ScheduleStore(path=sf)
    store.add(ScheduledJob(name="dup", command="echo", cron_expr="* * * * *"))

    args = make_args(
        schedule_cmd="add",
        schedules_file=sf,
        name="dup",
        command="echo",
        cron_expr="* * * * *",
        tags=[],
        description="",
    )
    cmd_schedule(args)
    out = capsys.readouterr().out
    assert "Error" in out


def test_cmd_remove_existing(tmp_path, capsys):
    sf = str(tmp_path / "s.json")
    store = ScheduleStore(path=sf)
    store.add(ScheduledJob(name="todel", command="echo", cron_expr="* * * * *"))

    args = make_args(schedule_cmd="remove", schedules_file=sf, name="todel")
    cmd_schedule(args)
    out = capsys.readouterr().out
    assert "removed" in out


def test_cmd_remove_nonexistent(tmp_path, capsys):
    sf = str(tmp_path / "s.json")
    args = make_args(schedule_cmd="remove", schedules_file=sf, name="ghost")
    cmd_schedule(args)
    out = capsys.readouterr().out
    assert "No scheduled job" in out


def test_cmd_next_prints_datetime(tmp_path, capsys):
    sf = str(tmp_path / "s.json")
    store = ScheduleStore(path=sf)
    store.add(ScheduledJob(name="hourly", command="echo", cron_expr="0 * * * *"))

    args = make_args(schedule_cmd="next", schedules_file=sf, name="hourly")
    cmd_schedule(args)
    out = capsys.readouterr().out
    assert "Next run" in out
    assert "hourly" in out


def test_cmd_next_unknown_job(tmp_path, capsys):
    sf = str(tmp_path / "s.json")
    args = make_args(schedule_cmd="next", schedules_file=sf, name="unknown")
    cmd_schedule(args)
    out = capsys.readouterr().out
    assert "No scheduled job" in out
