"""Tests for cronlog.correlation."""

from __future__ import annotations

import pytest

from cronlog.models import JobRun
from cronlog import correlation
from cronlog.correlation import (
    link_runs,
    get_correlated_ids,
    find_correlated_runs,
    get_correlation_id,
    all_correlation_ids,
    unregister_all,
)


def make_run(job_name: str = "job") -> JobRun:
    return JobRun(job_name=job_name)


@pytest.fixture(autouse=True)
def clean_correlation():
    unregister_all()
    yield
    unregister_all()


def test_link_runs_records_run_ids():
    r1 = make_run("job-a")
    r2 = make_run("job-b")
    link_runs("deploy-42", r1, r2)
    ids = get_correlated_ids("deploy-42")
    assert r1.run_id in ids
    assert r2.run_id in ids


def test_link_runs_is_idempotent():
    r1 = make_run()
    link_runs("cid", r1)
    link_runs("cid", r1)
    assert get_correlated_ids("cid").count(r1.run_id) == 1


def test_link_runs_normalises_correlation_id():
    r1 = make_run()
    link_runs("  CID-1  ", r1)
    assert r1.run_id in get_correlated_ids("cid-1")


def test_link_runs_sets_metadata_on_run():
    r1 = make_run()
    link_runs("batch-7", r1)
    assert r1.metadata.get("correlation_id") == "batch-7"


def test_link_runs_empty_id_raises():
    r1 = make_run()
    with pytest.raises(ValueError):
        link_runs("", r1)


def test_get_correlated_ids_unknown_returns_empty():
    assert get_correlated_ids("no-such-id") == []


def test_find_correlated_runs_filters_correctly():
    r1 = make_run("a")
    r2 = make_run("b")
    r3 = make_run("c")
    link_runs("grp", r1, r2)
    result = find_correlated_runs("grp", [r1, r2, r3])
    assert r1 in result
    assert r2 in result
    assert r3 not in result


def test_find_correlated_runs_empty_list():
    assert find_correlated_runs("grp", []) == []


def test_get_correlation_id_returns_none_when_not_set():
    r = make_run()
    assert get_correlation_id(r) is None


def test_get_correlation_id_returns_value_after_link():
    r = make_run()
    link_runs("my-corr", r)
    assert get_correlation_id(r) == "my-corr"


def test_all_correlation_ids_returns_all_keys():
    r1, r2 = make_run(), make_run()
    link_runs("alpha", r1)
    link_runs("beta", r2)
    ids = all_correlation_ids()
    assert "alpha" in ids
    assert "beta" in ids


def test_unregister_all_clears_state():
    link_runs("tmp", make_run())
    unregister_all()
    assert all_correlation_ids() == []
