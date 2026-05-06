"""Tests for cronlog.formatter."""

from datetime import datetime, timezone

import pytest

from cronlog.formatter import format_run_detail, format_run_row, format_run_table
from cronlog.models import JobRun, JobStatus


def make_finished_run(
    job_name: str = "backup",
    exit_code: int = 0,
    stdout: str = "done",
    stderr: str = "",
) -> JobRun:
    run = JobRun(job_name=job_name, command="/usr/bin/backup.sh")
    run.started_at = datetime(2024, 6, 15, 8, 30, 0, tzinfo=timezone.utc)
    run.finish(exit_code=exit_code, stdout=stdout, stderr=stderr)
    return run


def test_format_run_row_contains_job_name():
    run = make_finished_run()
    row = format_run_row(run, color=False)
    assert "backup" in row


def test_format_run_row_success_label():
    run = make_finished_run(exit_code=0)
    row = format_run_row(run, color=False)
    assert "OK" in row


def test_format_run_row_failure_label():
    run = make_finished_run(exit_code=1)
    row = format_run_row(run, color=False)
    assert "FAIL" in row


def test_format_run_row_contains_exit_code():
    run = make_finished_run(exit_code=2)
    row = format_run_row(run, color=False)
    assert "exit=2" in row


def test_format_run_row_contains_started_date():
    run = make_finished_run()
    row = format_run_row(run, color=False)
    assert "2024-06-15" in row


def test_format_run_detail_contains_run_id():
    run = make_finished_run()
    detail = format_run_detail(run, color=False)
    assert run.run_id in detail


def test_format_run_detail_contains_stdout():
    run = make_finished_run(stdout="hello output")
    detail = format_run_detail(run, color=False)
    assert "hello output" in detail
    assert "stdout" in detail


def test_format_run_detail_no_stderr_section_when_empty():
    run = make_finished_run(stderr="")
    detail = format_run_detail(run, color=False)
    assert "stderr" not in detail


def test_format_run_detail_contains_stderr_when_present():
    run = make_finished_run(stderr="something went wrong")
    detail = format_run_detail(run, color=False)
    assert "stderr" in detail
    assert "something went wrong" in detail


def test_format_run_table_empty():
    result = format_run_table([], color=False)
    assert result == "No runs found."


def test_format_run_table_contains_header():
    runs = [make_finished_run()]
    table = format_run_table(runs, color=False)
    assert "STARTED" in table
    assert "STATUS" in table
    assert "JOB" in table


def test_format_run_table_lists_all_runs():
    runs = [make_finished_run(job_name=f"job{i}") for i in range(3)]
    table = format_run_table(runs, color=False)
    for i in range(3):
        assert f"job{i}" in table
