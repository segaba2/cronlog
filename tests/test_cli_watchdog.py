"""Tests for cronlog.cli_watchdog."""

from __future__ import annotations

import argparse
import json
from unittest.mock import MagicMock, patch

import pytest

from cronlog.cli_watchdog import add_watchdog_subparser, cmd_watchdog


def make_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "log_dir": ".cronlog",
        "grace": 300,
        "as_json": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_watchdog_subparser_registers_command():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers()
    add_watchdog_subparser(sub)
    args = parser.parse_args(["watchdog"])
    assert hasattr(args, "func")


def test_cmd_watchdog_no_overdue_prints_ok(capsys):
    args = make_args()
    with (
        patch("cronlog.cli_watchdog.JobRunStorage"),
        patch("cronlog.cli_watchdog.watchdog_report", return_value=[]),
    ):
        cmd_watchdog(args)
    out = capsys.readouterr().out
    assert "on time" in out


def test_cmd_watchdog_overdue_shows_table(capsys):
    overdue = [
        {"job_name": "backup", "cron": "0 2 * * *",
         "last_due": "2024-06-01T02:00:00+00:00", "grace_seconds": 300}
    ]
    args = make_args()
    with (
        patch("cronlog.cli_watchdog.JobRunStorage"),
        patch("cronlog.cli_watchdog.watchdog_report", return_value=overdue),
    ):
        cmd_watchdog(args)
    out = capsys.readouterr().out
    assert "backup" in out
    assert "0 2 * * *" in out


def test_cmd_watchdog_json_flag_outputs_json(capsys):
    overdue = [
        {"job_name": "nightly", "cron": "0 3 * * *",
         "last_due": "2024-06-01T03:00:00+00:00", "grace_seconds": 300}
    ]
    args = make_args(as_json=True)
    with (
        patch("cronlog.cli_watchdog.JobRunStorage"),
        patch("cronlog.cli_watchdog.watchdog_report", return_value=overdue),
    ):
        cmd_watchdog(args)
    out = capsys.readouterr().out
    parsed = json.loads(out)
    assert parsed[0]["job_name"] == "nightly"


def test_cmd_watchdog_passes_grace_to_report():
    args = make_args(grace=120)
    with (
        patch("cronlog.cli_watchdog.JobRunStorage") as mock_storage,
        patch("cronlog.cli_watchdog.watchdog_report", return_value=[]) as mock_report,
    ):
        cmd_watchdog(args)
    mock_report.assert_called_once_with(
        mock_storage.return_value, args.log_dir, grace_seconds=120
    )
