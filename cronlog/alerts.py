"""Alert rules: trigger notifications when job runs meet defined conditions."""

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cronlog.models import JobRun, JobStatus


@dataclass
class AlertRule:
    name: str
    condition: Callable[[JobRun], bool]
    message: Callable[[JobRun], str]
    tags: List[str] = field(default_factory=list)


_rules: List[AlertRule] = []


def register_rule(rule: AlertRule) -> None:
    """Register an alert rule globally."""
    _rules.append(rule)


def unregister_all() -> None:
    """Remove all registered alert rules (useful for testing)."""
    _rules.clear()


def get_rules() -> List[AlertRule]:
    return list(_rules)


def evaluate_rules(run: JobRun, rules: Optional[List[AlertRule]] = None) -> List[str]:
    """Evaluate all matching rules against a run, returning triggered messages."""
    active_rules = rules if rules is not None else _rules
    triggered = []
    for rule in active_rules:
        try:
            if rule.condition(run):
                triggered.append(rule.message(run))
        except Exception:
            pass
    return triggered


def failure_alert_rule(job_name: Optional[str] = None) -> AlertRule:
    """Built-in rule: alert on any failure, optionally scoped to a job name."""
    def condition(run: JobRun) -> bool:
        if job_name and run.job_name != job_name:
            return False
        return run.status == JobStatus.FAILURE

    def message(run: JobRun) -> str:
        return f"[ALERT] Job '{run.job_name}' failed (exit {run.exit_code}) at {run.started_at}"

    return AlertRule(name="failure_alert", condition=condition, message=message)


def long_running_alert_rule(threshold_seconds: float, job_name: Optional[str] = None) -> AlertRule:
    """Built-in rule: alert when a job exceeds a duration threshold."""
    def condition(run: JobRun) -> bool:
        if job_name and run.job_name != job_name:
            return False
        if run.finished_at is None or run.started_at is None:
            return False
        duration = (run.finished_at - run.started_at).total_seconds()
        return duration > threshold_seconds

    def message(run: JobRun) -> str:
        duration = (run.finished_at - run.started_at).total_seconds()
        return (
            f"[ALERT] Job '{run.job_name}' ran for {duration:.1f}s "
            f"(threshold: {threshold_seconds}s) at {run.started_at}"
        )

    return AlertRule(name="long_running_alert", condition=condition, message=message)
