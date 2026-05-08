"""Tests for cronlog.annotations."""

import pytest
from cronlog.models import JobRun, JobStatus
from cronlog.annotations import (
    annotate,
    remove_annotation,
    get_annotation,
    filter_by_annotation,
    all_annotation_keys,
)


def make_run(job_name: str = "test-job") -> JobRun:
    run = JobRun(job_name=job_name)
    run.annotations = {}
    return run


# --- annotate ---

def test_annotate_adds_key_value():
    run = make_run()
    annotate(run, "env", "production")
    assert run.annotations["env"] == "production"


def test_annotate_normalises_key_to_lowercase():
    run = make_run()
    annotate(run, "ENV", "staging")
    assert "env" in run.annotations


def test_annotate_strips_key_whitespace():
    run = make_run()
    annotate(run, "  env  ", "dev")
    assert "env" in run.annotations


def test_annotate_ignores_empty_key():
    run = make_run()
    annotate(run, "", "value")
    assert run.annotations == {}


def test_annotate_overwrites_existing_key():
    run = make_run()
    annotate(run, "env", "staging")
    annotate(run, "env", "production")
    assert run.annotations["env"] == "production"


def test_annotate_works_when_annotations_is_none():
    run = make_run()
    run.annotations = None
    annotate(run, "note", "hello")
    assert run.annotations["note"] == "hello"


# --- remove_annotation ---

def test_remove_annotation_deletes_key():
    run = make_run()
    annotate(run, "env", "prod")
    remove_annotation(run, "env")
    assert "env" not in run.annotations


def test_remove_annotation_noop_on_missing_key():
    run = make_run()
    remove_annotation(run, "nonexistent")  # should not raise


# --- get_annotation ---

def test_get_annotation_returns_value():
    run = make_run()
    annotate(run, "team", "ops")
    assert get_annotation(run, "team") == "ops"


def test_get_annotation_returns_none_for_missing_key():
    run = make_run()
    assert get_annotation(run, "missing") is None


# --- filter_by_annotation ---

def test_filter_by_annotation_key_only():
    runs = [make_run("a"), make_run("b"), make_run("c")]
    annotate(runs[0], "env", "prod")
    annotate(runs[1], "env", "staging")
    result = filter_by_annotation(runs, "env")
    assert len(result) == 2


def test_filter_by_annotation_key_and_value():
    runs = [make_run("a"), make_run("b"), make_run("c")]
    annotate(runs[0], "env", "prod")
    annotate(runs[1], "env", "staging")
    result = filter_by_annotation(runs, "env", "prod")
    assert len(result) == 1
    assert result[0].job_name == "a"


def test_filter_by_annotation_returns_empty_when_no_match():
    runs = [make_run("a"), make_run("b")]
    result = filter_by_annotation(runs, "env")
    assert result == []


# --- all_annotation_keys ---

def test_all_annotation_keys_returns_sorted_unique_keys():
    runs = [make_run("a"), make_run("b")]
    annotate(runs[0], "env", "prod")
    annotate(runs[0], "team", "ops")
    annotate(runs[1], "env", "staging")
    keys = all_annotation_keys(runs)
    assert keys == ["env", "team"]


def test_all_annotation_keys_empty_runs():
    assert all_annotation_keys([]) == []
