"""Tests for cronlog.labeling."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from cronlog.labeling import (
    all_label_keys,
    filter_by_label,
    filter_has_label,
    get_label,
    labels_as_dict,
    remove_label,
    set_label,
)
from cronlog.models import JobRun, JobStatus


def make_run(job_name: str = "test-job") -> JobRun:
    run = JobRun(job_name=job_name)
    if not hasattr(run, "labels"):
        run.labels = {}
    return run


# --- set_label ---

def test_set_label_adds_key_value():
    run = make_run()
    set_label(run, "env", "production")
    assert run.labels["env"] == "production"


def test_set_label_normalises_key_to_lowercase():
    run = make_run()
    set_label(run, "ENV", "staging")
    assert "env" in run.labels
    assert run.labels["env"] == "staging"


def test_set_label_strips_key_whitespace():
    run = make_run()
    set_label(run, "  team  ", "ops")
    assert "team" in run.labels


def test_set_label_ignores_empty_key():
    run = make_run()
    set_label(run, "", "value")
    assert run.labels == {}


def test_set_label_overwrites_existing():
    run = make_run()
    set_label(run, "env", "staging")
    set_label(run, "env", "production")
    assert run.labels["env"] == "production"


# --- remove_label ---

def test_remove_label_deletes_key():
    run = make_run()
    set_label(run, "env", "prod")
    remove_label(run, "env")
    assert "env" not in run.labels


def test_remove_label_missing_key_is_noop():
    run = make_run()
    remove_label(run, "nonexistent")  # should not raise


# --- get_label ---

def test_get_label_returns_value():
    run = make_run()
    set_label(run, "owner", "alice")
    assert get_label(run, "owner") == "alice"


def test_get_label_returns_none_when_absent():
    run = make_run()
    assert get_label(run, "missing") is None


# --- filter_by_label ---

def test_filter_by_label_returns_matching_runs():
    runs = [make_run("a"), make_run("b"), make_run("c")]
    set_label(runs[0], "env", "prod")
    set_label(runs[2], "env", "prod")
    result = filter_by_label(runs, "env", "prod")
    assert len(result) == 2


def test_filter_by_label_empty_list():
    assert filter_by_label([], "env", "prod") == []


# --- filter_has_label ---

def test_filter_has_label_returns_runs_with_key():
    runs = [make_run("a"), make_run("b")]
    set_label(runs[0], "team", "ops")
    result = filter_has_label(runs, "team")
    assert result == [runs[0]]


# --- all_label_keys ---

def test_all_label_keys_returns_sorted_unique_keys():
    runs = [make_run(), make_run()]
    set_label(runs[0], "env", "prod")
    set_label(runs[1], "team", "ops")
    set_label(runs[1], "env", "staging")
    keys = all_label_keys(runs)
    assert keys == ["env", "team"]


def test_all_label_keys_empty_runs():
    assert all_label_keys([]) == []


# --- labels_as_dict ---

def test_labels_as_dict_returns_copy():
    run = make_run()
    set_label(run, "x", "1")
    d = labels_as_dict(run)
    d["x"] = "mutated"
    assert run.labels["x"] == "1"


def test_labels_as_dict_empty_returns_empty_dict():
    run = make_run()
    assert labels_as_dict(run) == {}
