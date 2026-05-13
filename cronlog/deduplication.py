"""Deduplication utilities for cronlog job runs.

Provides helpers to detect and remove duplicate job run entries,
based on run_id or on (job_name, started_at) identity.
"""

from __future__ import annotations

from typing import List

from cronlog.models import JobRun


def deduplicate_by_id(runs: List[JobRun]) -> List[JobRun]:
    """Return a list with duplicate run_ids removed, keeping the first occurrence."""
    seen: set = set()
    result: List[JobRun] = []
    for run in runs:
        if run.run_id not in seen:
            seen.add(run.run_id)
            result.append(run)
    return result


def deduplicate_by_identity(runs: List[JobRun]) -> List[JobRun]:
    """Return a list with duplicate (job_name, started_at) pairs removed.

    Keeps the first occurrence of each (job_name, started_at) pair.
    """
    seen: set = set()
    result: List[JobRun] = []
    for run in runs:
        key = (run.job_name, run.started_at)
        if key not in seen:
            seen.add(key)
            result.append(run)
    return result


def find_duplicates_by_id(runs: List[JobRun]) -> List[JobRun]:
    """Return all runs whose run_id appears more than once (excluding first occurrence)."""
    seen: set = set()
    duplicates: List[JobRun] = []
    for run in runs:
        if run.run_id in seen:
            duplicates.append(run)
        else:
            seen.add(run.run_id)
    return duplicates


def find_duplicates_by_identity(runs: List[JobRun]) -> List[JobRun]:
    """Return all runs whose (job_name, started_at) appears more than once."""
    seen: set = set()
    duplicates: List[JobRun] = []
    for run in runs:
        key = (run.job_name, run.started_at)
        if key in seen:
            duplicates.append(run)
        else:
            seen.add(key)
    return duplicates


def merge_run_lists(*lists: List[JobRun]) -> List[JobRun]:
    """Merge multiple run lists and deduplicate by run_id."""
    combined: List[JobRun] = []
    for lst in lists:
        combined.extend(lst)
    return deduplicate_by_id(combined)
