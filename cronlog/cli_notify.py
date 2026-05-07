"""CLI integration for notification configuration."""

import argparse
from cronlog.notify import register_handler, log_handler, failure_only_handler


def add_notify_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the 'notify' sub-command to an existing subparsers group."""
    parser = subparsers.add_parser(
        "notify",
        help="Configure and test notification hooks",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Emit a test notification using the built-in log handler",
    )
    parser.add_argument(
        "--failures-only",
        action="store_true",
        help="Only notify on failures when using --test",
    )
    parser.set_defaults(func=cmd_notify)


def cmd_notify(args: argparse.Namespace) -> None:
    """Handle the 'notify' sub-command."""
    if args.test:
        from cronlog.models import JobRun, JobStatus
        from datetime import datetime, timezone, timedelta

        run = JobRun(job_name="test-job")
        run.exit_code = 0
        run.status = JobStatus.SUCCESS
        run.stdout = "hello"
        run.stderr = ""
        run.finished_at = datetime.now(timezone.utc)
        run.started_at = run.finished_at - timedelta(seconds=2.5)

        handler = log_handler
        if args.failures_only:
            handler = failure_only_handler(log_handler)

        register_handler(handler)
        from cronlog.notify import notify
        notify(run)
        print("[cronlog] Test notification dispatched.")
    else:
        print("[cronlog] No action specified. Use --test to emit a test notification.")
