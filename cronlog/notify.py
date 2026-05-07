"""Notification hooks for cron job run outcomes."""

from typing import Callable, Optional
from cronlog.models import JobRun, JobStatus

# Registry of notification handlers
_handlers: list[Callable[[JobRun], None]] = []


def register_handler(handler: Callable[[JobRun], None]) -> None:
    """Register a notification handler to be called after each job run."""
    _handlers.append(handler)


def unregister_all() -> None:
    """Remove all registered handlers (useful for testing)."""
    _handlers.clear()


def notify(run: JobRun) -> None:
    """Dispatch a completed JobRun to all registered handlers."""
    for handler in _handlers:
        try:
            handler(run)
        except Exception as exc:  # noqa: BLE001
            # Handlers must not crash the main process
            print(f"[cronlog.notify] Handler {handler!r} raised: {exc}")


def log_handler(run: JobRun) -> None:
    """Built-in handler: print a one-line summary to stdout."""
    status_label = "SUCCESS" if run.status == JobStatus.SUCCESS else "FAILURE"
    duration = ""
    if run.started_at and run.finished_at:
        secs = (run.finished_at - run.started_at).total_seconds()
        duration = f" ({secs:.1f}s)"
    print(f"[cronlog] {run.job_name} -> {status_label}{duration} (exit={run.exit_code})")


def failure_only_handler(
    inner: Callable[[JobRun], None]
) -> Callable[[JobRun], None]:
    """Wrap a handler so it is only called on failures."""
    def _wrapped(run: JobRun) -> None:
        if run.status == JobStatus.FAILURE:
            inner(run)
    _wrapped.__name__ = f"failure_only({inner.__name__})"
    return _wrapped
