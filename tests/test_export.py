"""Tests for cronlog/export.py."""

import csv
import io
import json
from datetime import datetime, timezone

import pytest

from cronlog.models import JobRun, JobStatus
from cronlog.export import export_to_json, export_to_csv, export_runs


@pytest.fixture
def sample_runs():
    run1 = JobRun(job_name="backup", command="tar -czf /tmp/b.tar.gz /data")
    run1.finish(exit_code=0, stdout="done", stderr="")

    run2 = JobRun(job_name="cleanup", command="rm -rf /tmp/old")
    run2.finish(exit_code=1, stdout="", stderr="permission denied")

    return [run1, run2]


# --- JSON export ---

def test_export_to_json_returns_string(sample_runs):
    result = export_to_json(sample_runs)
    assert isinstance(result, str)


def test_export_to_json_is_valid_json(sample_runs):
    result = export_to_json(sample_runs)
    data = json.loads(result)
    assert isinstance(data, list)
    assert len(data) == 2


def test_export_to_json_contains_job_names(sample_runs):
    result = export_to_json(sample_runs)
    data = json.loads(result)
    names = [r["job_name"] for r in data]
    assert "backup" in names
    assert "cleanup" in names


def test_export_to_json_empty_list():
    result = export_to_json([])
    assert json.loads(result) == []


# --- CSV export ---

def test_export_to_csv_returns_string(sample_runs):
    result = export_to_csv(sample_runs)
    assert isinstance(result, str)


def test_export_to_csv_has_header(sample_runs):
    result = export_to_csv(sample_runs)
    first_line = result.splitlines()[0]
    assert "job_name" in first_line
    assert "status" in first_line


def test_export_to_csv_row_count(sample_runs):
    result = export_to_csv(sample_runs)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 2


def test_export_to_csv_empty_list():
    result = export_to_csv([])
    assert result == ""


def test_export_to_csv_exit_codes(sample_runs):
    result = export_to_csv(sample_runs)
    reader = csv.DictReader(io.StringIO(result))
    rows = {r["job_name"]: r for r in reader}
    assert rows["backup"]["exit_code"] == "0"
    assert rows["cleanup"]["exit_code"] == "1"


# --- export_runs dispatcher ---

def test_export_runs_json(sample_runs):
    result = export_runs(sample_runs, "json")
    assert json.loads(result)[0]["job_name"] == "backup"


def test_export_runs_csv(sample_runs):
    result = export_runs(sample_runs, "csv")
    assert "backup" in result


def test_export_runs_invalid_format(sample_runs):
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_runs(sample_runs, "xml")
