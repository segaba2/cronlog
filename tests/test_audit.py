"""Tests for cronlog.audit."""

from __future__ import annotations

import os
import pytest

from cronlog.audit import (
    record_event,
    load_events,
    filter_events_by_type,
    clear_audit_log,
)


@pytest.fixture()
def log_dir(tmp_path):
    return str(tmp_path / "logs")


def test_record_event_creates_audit_file(log_dir):
    record_event(log_dir, "run_start", {"job": "backup"})
    assert os.path.exists(os.path.join(log_dir, "audit.log"))


def test_record_event_returns_entry(log_dir):
    entry = record_event(log_dir, "run_finish", {"exit_code": 0})
    assert entry["event"] == "run_finish"
    assert entry["details"]["exit_code"] == 0
    assert "timestamp" in entry


def test_load_events_empty_when_no_file(log_dir):
    events = load_events(log_dir)
    assert events == []


def test_load_events_returns_recorded_events(log_dir):
    record_event(log_dir, "run_start", {"job": "sync"})
    record_event(log_dir, "run_finish", {"job": "sync", "status": "success"})
    events = load_events(log_dir)
    assert len(events) == 2


def test_load_events_preserves_order(log_dir):
    record_event(log_dir, "first", {})
    record_event(log_dir, "second", {})
    events = load_events(log_dir)
    assert events[0]["event"] == "first"
    assert events[1]["event"] == "second"


def test_filter_events_by_type_returns_matching(log_dir):
    record_event(log_dir, "run_start", {})
    record_event(log_dir, "prune", {"removed": 3})
    record_event(log_dir, "run_start", {})
    events = load_events(log_dir)
    filtered = filter_events_by_type(events, "run_start")
    assert len(filtered) == 2
    assert all(e["event"] == "run_start" for e in filtered)


def test_filter_events_by_type_no_match(log_dir):
    record_event(log_dir, "run_start", {})
    events = load_events(log_dir)
    filtered = filter_events_by_type(events, "nonexistent")
    assert filtered == []


def test_clear_audit_log_removes_file(log_dir):
    record_event(log_dir, "run_start", {})
    clear_audit_log(log_dir)
    assert not os.path.exists(os.path.join(log_dir, "audit.log"))


def test_clear_audit_log_noop_when_no_file(log_dir):
    # Should not raise
    clear_audit_log(log_dir)


def test_record_event_no_details_defaults_to_empty_dict(log_dir):
    entry = record_event(log_dir, "heartbeat")
    assert entry["details"] == {}


def test_multiple_events_appended_not_overwritten(log_dir):
    for i in range(5):
        record_event(log_dir, "tick", {"i": i})
    events = load_events(log_dir)
    assert len(events) == 5
