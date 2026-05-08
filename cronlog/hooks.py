"""Pre/post execution hooks for cron job runs."""

from typing import Callable, List, Optional
from cronlog.models import JobRun

_pre_hooks: List[Callable[[JobRun], None]] = []
_post_hooks: List[Callable[[JobRun], None]] = []


def register_pre_hook(fn: Callable[[JobRun], None]) -> None:
    """Register a hook to be called before a job run starts."""
    _pre_hooks.append(fn)


def register_post_hook(fn: Callable[[JobRun], None]) -> None:
    """Register a hook to be called after a job run finishes."""
    _post_hooks.append(fn)


def unregister_all() -> None:
    """Remove all registered hooks (useful for testing)."""
    _pre_hooks.clear()
    _post_hooks.clear()


def run_pre_hooks(run: JobRun) -> None:
    """Execute all registered pre-hooks for the given run."""
    for hook in _pre_hooks:
        try:
            hook(run)
        except Exception:
            pass


def run_post_hooks(run: JobRun) -> None:
    """Execute all registered post-hooks for the given run."""
    for hook in _post_hooks:
        try:
            hook(run)
        except Exception:
            pass


def logging_pre_hook(run: JobRun) -> None:
    """Built-in pre-hook that prints a start message."""
    print(f"[cronlog] Starting job: {run.job_name} (run_id={run.run_id})")


def logging_post_hook(run: JobRun) -> None:
    """Built-in post-hook that prints a completion message."""
    status = run.status.value if run.status else "unknown"
    print(f"[cronlog] Finished job: {run.job_name} status={status} (run_id={run.run_id})")
