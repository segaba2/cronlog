"""High-level query interface combining storage, filters, and formatting."""

from datetime import datetime
from typing import List, Optional

from cronlog.filters import apply_filters, latest_per_job
from cronlog.formatter import format_run_detail, format_run_table
from cronlog.models import JobRun, JobStatus
from cronlog.storage import JobRunStorage


class JobRunQuery:
    """Convenience wrapper for querying stored job runs."""

    def __init__(self, storage: JobRunStorage) -> None:
        self._storage = storage

    def all(self) -> List[JobRun]:
        """Return all stored runs, newest first."""
        return apply_filters(self._storage.load_all())

    def for_job(self, job_name: str) -> List[JobRun]:
        """Return all runs for a specific job, newest first."""
        return apply_filters(self._storage.load_all(), job_name=job_name)

    def failures(self, job_name: Optional[str] = None) -> List[JobRun]:
        """Return failed runs, optionally scoped to a job."""
        return apply_filters(
            self._storage.load_all(),
            job_name=job_name,
            status=JobStatus.FAILURE,
        )

    def since(self, when: datetime, job_name: Optional[str] = None) -> List[JobRun]:
        """Return runs started at or after *when*."""
        return apply_filters(
            self._storage.load_all(),
            job_name=job_name,
            since=when,
        )

    def latest(self) -> List[JobRun]:
        """Return the most recent run per job."""
        return latest_per_job(self._storage.load_all())

    def get(self, run_id: str) -> Optional[JobRun]:
        """Retrieve a single run by its ID.

        Raises:
            ValueError: If *run_id* is empty or whitespace.
        """
        if not run_id or not run_id.strip():
            raise ValueError("run_id must be a non-empty string")
        for run in self._storage.load_all():
            if run.run_id == run_id:
                return run
        return None

    def print_table(
        self,
        job_name: Optional[str] = None,
        status: Optional[JobStatus] = None,
        since: Optional[datetime] = None,
        color: bool = True,
    ) -> str:
        """Return a formatted table string ready for printing."""
        runs = apply_filters(
            self._storage.load_all(),
            job_name=job_name,
            status=status,
            since=since,
        )
        return format_run_table(runs, color=color)

    def print_detail(self, run_id: str, color: bool = True) -> Optional[str]:
        """Return a formatted detail string for a single run, or None."""
        run = self.get(run_id)
        if run is None:
            return None
        return format_run_detail(run, color=color)
