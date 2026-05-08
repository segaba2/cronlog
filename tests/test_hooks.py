"""Tests for cronlog.hooks."""

import pytest
from cronlog.hooks import (
    register_pre_hook,
    register_post_hook,
    unregister_all,
    run_pre_hooks,
    run_post_hooks,
    logging_pre_hook,
    logging_post_hook,
    _pre_hooks,
    _post_hooks,
)
from cronlog.models import JobRun, JobStatus


@pytest.fixture(autouse=True)
def clean_hooks():
    unregister_all()
    yield
    unregister_all()


def _make_run(job_name="test-job"):
    return JobRun(job_name=job_name, command="echo hi")


def test_register_pre_hook_adds_to_list():
    fn = lambda run: None
    register_pre_hook(fn)
    assert fn in _pre_hooks


def test_register_post_hook_adds_to_list():
    fn = lambda run: None
    register_post_hook(fn)
    assert fn in _post_hooks


def test_unregister_all_clears_both_lists():
    register_pre_hook(lambda r: None)
    register_post_hook(lambda r: None)
    unregister_all()
    assert len(_pre_hooks) == 0
    assert len(_post_hooks) == 0


def test_run_pre_hooks_calls_registered_hook():
    called_with = []
    register_pre_hook(lambda r: called_with.append(r.job_name))
    run = _make_run("myjob")
    run_pre_hooks(run)
    assert called_with == ["myjob"]


def test_run_post_hooks_calls_registered_hook():
    called_with = []
    register_post_hook(lambda r: called_with.append(r.job_name))
    run = _make_run("postjob")
    run_post_hooks(run)
    assert called_with == ["postjob"]


def test_run_pre_hooks_calls_multiple_hooks():
    results = []
    register_pre_hook(lambda r: results.append("hook1"))
    register_pre_hook(lambda r: results.append("hook2"))
    run_pre_hooks(_make_run())
    assert results == ["hook1", "hook2"]


def test_run_pre_hooks_swallows_exceptions():
    def bad_hook(run):
        raise RuntimeError("boom")

    register_pre_hook(bad_hook)
    run_pre_hooks(_make_run())  # should not raise


def test_run_post_hooks_swallows_exceptions():
    def bad_hook(run):
        raise ValueError("oops")

    register_post_hook(bad_hook)
    run_post_hooks(_make_run())  # should not raise


def test_logging_pre_hook_prints(capsys):
    run = _make_run("print-job")
    logging_pre_hook(run)
    out = capsys.readouterr().out
    assert "print-job" in out
    assert run.run_id in out


def test_logging_post_hook_prints_status(capsys):
    run = _make_run("done-job")
    run.finish(exit_code=0, stdout="", stderr="")
    logging_post_hook(run)
    out = capsys.readouterr().out
    assert "done-job" in out
    assert "success" in out
