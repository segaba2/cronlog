"""Annotations support for job runs — attach arbitrary key/value notes to a run."""

from typing import Dict, List, Optional
from cronlog.models import JobRun


def annotate(run: JobRun, key: str, value: str) -> JobRun:
    """Add or update an annotation on a job run.

    Keys are normalised to lowercase and stripped of whitespace.
    Empty keys are silently ignored.
    """
    key = key.strip().lower()
    if not key:
        return run
    if not hasattr(run, "annotations") or run.annotations is None:
        run.annotations = {}
    run.annotations[key] = value
    return run


def remove_annotation(run: JobRun, key: str) -> JobRun:
    """Remove an annotation by key. No-op if the key does not exist."""
    key = key.strip().lower()
    if hasattr(run, "annotations") and run.annotations and key in run.annotations:
        del run.annotations[key]
    return run


def get_annotation(run: JobRun, key: str) -> Optional[str]:
    """Return the value for a given annotation key, or None."""
    key = key.strip().lower()
    if not hasattr(run, "annotations") or not run.annotations:
        return None
    return run.annotations.get(key)


def filter_by_annotation(runs: List[JobRun], key: str, value: Optional[str] = None) -> List[JobRun]:
    """Return runs that have the given annotation key (and optionally a specific value)."""
    key = key.strip().lower()
    result = []
    for run in runs:
        annotations: Dict[str, str] = getattr(run, "annotations", None) or {}
        if key in annotations:
            if value is None or annotations[key] == value:
                result.append(run)
    return result


def all_annotation_keys(runs: List[JobRun]) -> List[str]:
    """Return a sorted list of all unique annotation keys across the given runs."""
    keys = set()
    for run in runs:
        annotations: Dict[str, str] = getattr(run, "annotations", None) or {}
        keys.update(annotations.keys())
    return sorted(keys)
