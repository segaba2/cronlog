"""Labeling module: attach and query free-form labels on job runs."""

from __future__ import annotations

from typing import Dict, List

from cronlog.models import JobRun


def set_label(run: JobRun, key: str, value: str) -> JobRun:
    """Attach a label (key=value) to *run*.

    Keys are normalised to lowercase and stripped of surrounding whitespace.
    Empty keys are silently ignored.
    """
    key = key.strip().lower()
    if not key:
        return run
    if not hasattr(run, "labels") or run.labels is None:
        run.labels = {}
    run.labels[key] = value
    return run


def remove_label(run: JobRun, key: str) -> JobRun:
    """Remove label *key* from *run* if present."""
    key = key.strip().lower()
    if hasattr(run, "labels") and run.labels and key in run.labels:
        del run.labels[key]
    return run


def get_label(run: JobRun, key: str) -> str | None:
    """Return the value for *key* on *run*, or ``None`` if absent."""
    key = key.strip().lower()
    if not hasattr(run, "labels") or not run.labels:
        return None
    return run.labels.get(key)


def filter_by_label(runs: List[JobRun], key: str, value: str) -> List[JobRun]:
    """Return runs whose label *key* equals *value*."""
    key = key.strip().lower()
    return [
        r for r in runs
        if hasattr(r, "labels") and r.labels and r.labels.get(key) == value
    ]


def filter_has_label(runs: List[JobRun], key: str) -> List[JobRun]:
    """Return runs that have *key* set (regardless of value)."""
    key = key.strip().lower()
    return [
        r for r in runs
        if hasattr(r, "labels") and r.labels and key in r.labels
    ]


def all_label_keys(runs: List[JobRun]) -> List[str]:
    """Return a sorted list of all distinct label keys across *runs*."""
    keys: set[str] = set()
    for r in runs:
        if hasattr(r, "labels") and r.labels:
            keys.update(r.labels.keys())
    return sorted(keys)


def labels_as_dict(run: JobRun) -> Dict[str, str]:
    """Return a copy of the labels dict for *run* (empty dict if none)."""
    if not hasattr(run, "labels") or not run.labels:
        return {}
    return dict(run.labels)
