"""Tag support for job runs — attach, remove, and filter by tags."""

from typing import List
from cronlog.models import JobRun


def add_tag(run: JobRun, tag: str) -> JobRun:
    """Return a new JobRun dict-compatible object with the tag added."""
    current = list(run.tags) if hasattr(run, "tags") and run.tags else []
    tag = tag.strip().lower()
    if tag and tag not in current:
        current.append(tag)
    run.tags = current
    return run


def remove_tag(run: JobRun, tag: str) -> JobRun:
    """Return the run with the specified tag removed (if present)."""
    tag = tag.strip().lower()
    current = list(run.tags) if hasattr(run, "tags") and run.tags else []
    run.tags = [t for t in current if t != tag]
    return run


def filter_by_tag(runs: List[JobRun], tag: str) -> List[JobRun]:
    """Return only runs that have the given tag."""
    tag = tag.strip().lower()
    return [
        r for r in runs
        if hasattr(r, "tags") and r.tags and tag in r.tags
    ]


def filter_by_any_tag(runs: List[JobRun], tags: List[str]) -> List[JobRun]:
    """Return runs that have at least one of the given tags."""
    tags = {t.strip().lower() for t in tags}
    return [
        r for r in runs
        if hasattr(r, "tags") and r.tags and tags.intersection(r.tags)
    ]


def all_tags(runs: List[JobRun]) -> List[str]:
    """Return a sorted list of all unique tags across all runs."""
    seen = set()
    for r in runs:
        if hasattr(r, "tags") and r.tags:
            seen.update(r.tags)
    return sorted(seen)
