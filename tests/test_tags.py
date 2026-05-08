"""Tests for cronlog/tags.py"""

import pytest
from cronlog.models import JobRun
from cronlog.tags import (
    add_tag,
    remove_tag,
    filter_by_tag,
    filter_by_any_tag,
    all_tags,
)


def make_run(job_name: str, tags=None) -> JobRun:
    run = JobRun(job_name=job_name)
    run.tags = list(tags) if tags else []
    return run


# --- add_tag ---

def test_add_tag_adds_new_tag():
    run = make_run("backup")
    run = add_tag(run, "critical")
    assert "critical" in run.tags


def test_add_tag_is_idempotent():
    run = make_run("backup", tags=["critical"])
    run = add_tag(run, "critical")
    assert run.tags.count("critical") == 1


def test_add_tag_normalises_to_lowercase():
    run = make_run("backup")
    run = add_tag(run, "  PROD  ")
    assert "prod" in run.tags


def test_add_tag_ignores_empty_string():
    run = make_run("backup")
    run = add_tag(run, "   ")
    assert run.tags == []


# --- remove_tag ---

def test_remove_tag_removes_existing_tag():
    run = make_run("backup", tags=["critical", "prod"])
    run = remove_tag(run, "critical")
    assert "critical" not in run.tags
    assert "prod" in run.tags


def test_remove_tag_noop_when_tag_absent():
    run = make_run("backup", tags=["prod"])
    run = remove_tag(run, "staging")
    assert run.tags == ["prod"]


# --- filter_by_tag ---

def test_filter_by_tag_returns_matching_runs():
    runs = [
        make_run("a", tags=["critical"]),
        make_run("b", tags=["routine"]),
        make_run("c", tags=["critical", "prod"]),
    ]
    result = filter_by_tag(runs, "critical")
    assert len(result) == 2
    assert all("critical" in r.tags for r in result)


def test_filter_by_tag_returns_empty_when_no_match():
    runs = [make_run("a", tags=["routine"])]
    assert filter_by_tag(runs, "critical") == []


def test_filter_by_tag_handles_runs_without_tags():
    runs = [make_run("a"), make_run("b", tags=["critical"])]
    result = filter_by_tag(runs, "critical")
    assert len(result) == 1


# --- filter_by_any_tag ---

def test_filter_by_any_tag_matches_at_least_one():
    runs = [
        make_run("a", tags=["critical"]),
        make_run("b", tags=["staging"]),
        make_run("c", tags=["routine"]),
    ]
    result = filter_by_any_tag(runs, ["critical", "staging"])
    assert len(result) == 2


def test_filter_by_any_tag_empty_tag_list_returns_nothing():
    runs = [make_run("a", tags=["critical"])]
    assert filter_by_any_tag(runs, []) == []


# --- all_tags ---

def test_all_tags_returns_sorted_unique_tags():
    runs = [
        make_run("a", tags=["prod", "critical"]),
        make_run("b", tags=["staging", "prod"]),
    ]
    assert all_tags(runs) == ["critical", "prod", "staging"]


def test_all_tags_empty_list():
    assert all_tags([]) == []
