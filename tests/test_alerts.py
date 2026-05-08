"""Tests for cronlog.alerts module."""

import pytest
from datetime import datetime, timedelta, timezone

from cronlog.alerts import (
    AlertRule,
    evaluate_rules,
    failure_alert_rule,
    long_running_alert_rule,
    register_rule,
    unregister_all,
    get_rules,
)
from cronlog.models import JobRun, JobStatus


def _make_run(job_name="backup", status=JobStatus.SUCCESS, exit_code=0,
             duration_seconds=5.0):
    now = datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)
    run = JobRun(job_name=job_name)
    run.status = status
    run.exit_code = exit_code
    run.started_at = now
    run.finished_at = now + timedelta(seconds=duration_seconds)
    return run


@pytest.fixture(autouse=True)
def clean_rules():
    unregister_all()
    yield
    unregister_all()


def test_evaluate_rules_returns_empty_when_no_rules():
    run = _make_run()
    assert evaluate_rules(run) == []


def test_failure_alert_triggers_on_failure():
    rule = failure_alert_rule()
    run = _make_run(status=JobStatus.FAILURE, exit_code=1)
    messages = evaluate_rules(run, rules=[rule])
    assert len(messages) == 1
    assert "ALERT" in messages[0]
    assert "backup" in messages[0]


def test_failure_alert_does_not_trigger_on_success():
    rule = failure_alert_rule()
    run = _make_run(status=JobStatus.SUCCESS, exit_code=0)
    messages = evaluate_rules(run, rules=[rule])
    assert messages == []


def test_failure_alert_scoped_to_job_name_matches():
    rule = failure_alert_rule(job_name="backup")
    run = _make_run(job_name="backup", status=JobStatus.FAILURE, exit_code=1)
    assert len(evaluate_rules(run, rules=[rule])) == 1


def test_failure_alert_scoped_to_job_name_skips_other_jobs():
    rule = failure_alert_rule(job_name="backup")
    run = _make_run(job_name="sync", status=JobStatus.FAILURE, exit_code=1)
    assert evaluate_rules(run, rules=[rule]) == []


def test_long_running_alert_triggers_when_over_threshold():
    rule = long_running_alert_rule(threshold_seconds=10.0)
    run = _make_run(duration_seconds=30.0)
    messages = evaluate_rules(run, rules=[rule])
    assert len(messages) == 1
    assert "30.0s" in messages[0]


def test_long_running_alert_does_not_trigger_when_under_threshold():
    rule = long_running_alert_rule(threshold_seconds=60.0)
    run = _make_run(duration_seconds=5.0)
    assert evaluate_rules(run, rules=[rule]) == []


def test_multiple_rules_can_trigger_together():
    rules = [failure_alert_rule(), long_running_alert_rule(threshold_seconds=10.0)]
    run = _make_run(status=JobStatus.FAILURE, exit_code=1, duration_seconds=60.0)
    messages = evaluate_rules(run, rules=rules)
    assert len(messages) == 2


def test_register_rule_adds_to_global_registry():
    rule = failure_alert_rule()
    register_rule(rule)
    assert rule in get_rules()


def test_evaluate_rules_uses_global_registry_by_default():
    rule = failure_alert_rule()
    register_rule(rule)
    run = _make_run(status=JobStatus.FAILURE, exit_code=1)
    messages = evaluate_rules(run)
    assert len(messages) == 1


def test_evaluate_rules_swallows_bad_condition():
    def bad_condition(run):
        raise RuntimeError("oops")

    rule = AlertRule(name="bad", condition=bad_condition, message=lambda r: "x")
    run = _make_run()
    assert evaluate_rules(run, rules=[rule]) == []
