"""Tests for the CLI prune subcommand."""

import argparse
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cronlog.cli_retention import add_retention_subparser, cmd_prune


def make_args(**kwargs):
    defaults = {
        "max_age_days": None,
        "max_count": None,
        "max_per_job": None,
        "log_file": Path("/tmp/test_runs.jsonl"),
        "dry_run": False,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_add_retention_subparser_registers_prune():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()
    add_retention_subparser(subparsers)
    args = parser.parse_args(["prune", "--max-age-days", "30"])
    assert args.max_age_days == 30


def test_cmd_prune_no_policy_prints_error(capsys):
    args = make_args()
    cmd_prune(args)
    out = capsys.readouterr().out
    assert "Error" in out


def test_cmd_prune_calls_apply_retention(capsys):
    args = make_args(max_age_days=7)
    with patch("cronlog.cli_retention.JobRunStorage") as MockStorage, \
         patch("cronlog.cli_retention.apply_retention", return_value=3) as mock_apply:
        cmd_prune(args)
        mock_apply.assert_called_once()
        out = capsys.readouterr().out
        assert "3" in out


def test_cmd_prune_dry_run_does_not_save(capsys):
    from cronlog.models import JobRun, JobStatus
    from datetime import datetime, timezone, timedelta

    run = JobRun(job_name="job", command="echo hi")
    run.started_at = datetime.now(timezone.utc) - timedelta(days=100)
    run.status = JobStatus.SUCCESS
    run.exit_code = 0
    run.finished_at = run.started_at + timedelta(seconds=1)

    args = make_args(max_age_days=7, dry_run=True)
    with patch("cronlog.cli_retention.JobRunStorage") as MockStorage:
        instance = MockStorage.return_value
        instance.load_all.return_value = [run]
        cmd_prune(args)
        instance.save_all.assert_not_called()
        out = capsys.readouterr().out
        assert "Dry run" in out
        assert "1" in out
