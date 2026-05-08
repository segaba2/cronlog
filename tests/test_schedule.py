"""Tests for cronlog.schedule."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from cronlog.schedule import ScheduledJob, ScheduleStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def store(tmp_path):
    return ScheduleStore(path=tmp_path / "schedules.json")


@pytest.fixture
def sample_job():
    return ScheduledJob(
        name="backup",
        command="/usr/bin/backup.sh",
        cron_expr="0 2 * * *",
        tags=["nightly"],
        description="Nightly backup",
    )


# ---------------------------------------------------------------------------
# ScheduledJob unit tests
# ---------------------------------------------------------------------------

def test_next_run_returns_datetime(sample_job):
    nxt = sample_job.next_run()
    assert isinstance(nxt, datetime)
    assert nxt.tzinfo is not None


def test_next_run_is_in_the_future(sample_job):
    now = datetime.now(timezone.utc)
    assert sample_job.next_run(now) > now


def test_is_due_false_for_distant_future(sample_job):
    # A job scheduled hourly should not be due within 0-second window
    job = ScheduledJob(name="hourly", command="echo hi", cron_expr="0 * * * *")
    assert not job.is_due(window_seconds=0)


def test_to_dict_roundtrip(sample_job):
    d = sample_job.to_dict()
    restored = ScheduledJob.from_dict(d)
    assert restored.name == sample_job.name
    assert restored.command == sample_job.command
    assert restored.cron_expr == sample_job.cron_expr
    assert restored.tags == sample_job.tags


def test_enabled_defaults_to_true():
    job = ScheduledJob(name="j", command="echo", cron_expr="* * * * *")
    assert job.enabled is True


# ---------------------------------------------------------------------------
# ScheduleStore tests
# ---------------------------------------------------------------------------

def test_all_returns_empty_when_no_file(store):
    assert store.all() == []


def test_add_persists_job(store, sample_job):
    store.add(sample_job)
    jobs = store.all()
    assert len(jobs) == 1
    assert jobs[0].name == "backup"


def test_add_duplicate_raises(store, sample_job):
    store.add(sample_job)
    with pytest.raises(ValueError, match="already exists"):
        store.add(sample_job)


def test_get_returns_job(store, sample_job):
    store.add(sample_job)
    found = store.get("backup")
    assert found is not None
    assert found.command == sample_job.command


def test_get_returns_none_for_unknown(store):
    assert store.get("ghost") is None


def test_remove_deletes_job(store, sample_job):
    store.add(sample_job)
    removed = store.remove("backup")
    assert removed is True
    assert store.all() == []


def test_remove_returns_false_when_not_found(store):
    assert store.remove("nonexistent") is False


def test_file_is_valid_json(store, sample_job, tmp_path):
    store.add(sample_job)
    raw = json.loads((tmp_path / "schedules.json").read_text())
    assert isinstance(raw, list)
    assert raw[0]["name"] == "backup"
