"""Run diffing: compare two job runs and highlight differences in metadata."""

from __future__ import annotations

from typing import Any

from cronlog.models import JobRun

_COMPARABLE_FIELDS = (
    "job_name",
    "exit_code",
    "status",
    "stdout",
    "stderr",
    "tags",
    "labels",
    "annotations",
)


def diff_runs(a: JobRun, b: JobRun) -> dict[str, dict[str, Any]]:
    """Return a mapping of field -> {"a": value, "b": value} for fields that differ."""
    differences: dict[str, dict[str, Any]] = {}
    for field in _COMPARABLE_FIELDS:
        val_a = getattr(a, field, None)
        val_b = getattr(b, field, None)
        if val_a != val_b:
            differences[field] = {"a": val_a, "b": val_b}
    return differences


def duration_diff_seconds(a: JobRun, b: JobRun) -> float | None:
    """Return the difference in duration (b - a) in seconds, or None if either run lacks timestamps."""
    if a.started_at is None or a.finished_at is None:
        return None
    if b.started_at is None or b.finished_at is None:
        return None
    dur_a = (a.finished_at - a.started_at).total_seconds()
    dur_b = (b.finished_at - b.started_at).total_seconds()
    return dur_b - dur_a


def summarise_diff(a: JobRun, b: JobRun) -> dict[str, Any]:
    """Return a human-readable summary dict comparing two runs."""
    field_diffs = diff_runs(a, b)
    dur_diff = duration_diff_seconds(a, b)
    return {
        "run_a": a.run_id,
        "run_b": b.run_id,
        "changed_fields": list(field_diffs.keys()),
        "differences": field_diffs,
        "duration_diff_seconds": dur_diff,
    }


def runs_are_equivalent(a: JobRun, b: JobRun) -> bool:
    """Return True if the two runs have no differences in comparable fields."""
    return len(diff_runs(a, b)) == 0
