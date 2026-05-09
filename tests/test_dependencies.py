"""Tests for cronlog.dependencies."""

import pytest

import cronlog.dependencies as deps
from cronlog.models import JobRun, JobStatus


@pytest.fixture(autouse=True)
def clean_deps():
    deps.unregister_all()
    yield
    deps.unregister_all()


def _make_run(job_name: str, status: str) -> dict:
    return {"job_name": job_name, "status": status}


def test_register_dependency_adds_edge():
    deps.register_dependency("b", "a")
    assert "a" in deps.get_dependencies("b")


def test_register_dependency_is_idempotent():
    deps.register_dependency("b", "a")
    deps.register_dependency("b", "a")
    assert deps.get_dependencies("b").count("a") == 1


def test_register_dependency_normalises_case():
    deps.register_dependency("JobB", "JobA")
    assert "joba" in deps.get_dependencies("jobb")


def test_register_dependency_self_raises():
    with pytest.raises(ValueError):
        deps.register_dependency("a", "a")


def test_register_dependency_ignores_empty():
    deps.register_dependency("", "a")
    deps.register_dependency("b", "")
    assert deps.all_dependencies() == {}


def test_unregister_dependency_removes_edge():
    deps.register_dependency("b", "a")
    deps.register_dependency("b", "c")
    deps.unregister_dependency("b", "a")
    assert "a" not in deps.get_dependencies("b")
    assert "c" in deps.get_dependencies("b")


def test_unregister_all_clears_map():
    deps.register_dependency("b", "a")
    deps.unregister_all()
    assert deps.all_dependencies() == {}


def test_is_satisfied_no_deps_returns_true():
    runs = [_make_run("a", "success")]
    assert deps.is_satisfied("b", runs) is True


def test_is_satisfied_dep_succeeded():
    deps.register_dependency("b", "a")
    runs = [_make_run("a", "success")]
    assert deps.is_satisfied("b", runs) is True


def test_is_satisfied_dep_failed():
    deps.register_dependency("b", "a")
    runs = [_make_run("a", "failure")]
    assert deps.is_satisfied("b", runs) is False


def test_is_satisfied_dep_missing():
    deps.register_dependency("b", "a")
    assert deps.is_satisfied("b", []) is False


def test_is_satisfied_multiple_deps_all_must_succeed():
    deps.register_dependency("c", "a")
    deps.register_dependency("c", "b")
    runs = [_make_run("a", "success"), _make_run("b", "failure")]
    assert deps.is_satisfied("c", runs) is False


def test_is_satisfied_accepts_jobrun_objects():
    deps.register_dependency("b", "a")
    run = JobRun(job_name="a", command="echo hi")
    run.finish(exit_code=0, stdout="", stderr="")
    assert deps.is_satisfied("b", [run]) is True


def test_detect_cycles_returns_none_when_no_cycle():
    deps.register_dependency("b", "a")
    deps.register_dependency("c", "b")
    assert deps.detect_cycles() is None


def test_detect_cycles_finds_simple_cycle():
    deps.register_dependency("a", "b")
    deps.register_dependency("b", "a")
    cycle = deps.detect_cycles()
    assert cycle is not None
    assert len(cycle) >= 2
