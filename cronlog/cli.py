"""Main CLI entry point for cronlog."""

from __future__ import annotations

import argparse
import sys

from cronlog.storage import JobRunStorage
from cronlog.runner import run_job
from cronlog.formatter import format_run_table
from cronlog.filters import filter_by_status, filter_by_job_name, filter_since
from cronlog.cli_export import add_export_subparser, cmd_export
from cronlog.cli_stats import add_stats_subparser, cmd_stats
from cronlog.cli_notify import add_notify_subparser, cmd_notify
from cronlog.cli_retention import add_retention_subparser, cmd_prune
from cronlog.cli_tags import add_tags_subparser, cmd_tags
from cronlog.cli_alerts import add_alerts_subparser, cmd_alerts
from cronlog.cli_schedule import add_schedule_subparser, cmd_schedule
from cronlog.cli_hooks import add_hooks_subparser, cmd_hooks
from cronlog.cli_annotations import add_annotations_subparser, cmd_annotations
from cronlog.cli_dependencies import add_dependencies_subparser, cmd_deps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronlog",
        description="Lightweight cron job output capture and querying.",
    )
    parser.add_argument(
        "--log-dir",
        default=".cronlog",
        help="Directory where job logs are stored (default: .cronlog)",
    )

    subparsers = parser.add_subparsers(dest="command")

    # run
    run_p = subparsers.add_parser("run", help="Run a command and log its output")
    run_p.add_argument("job_name", help="Logical name for this job")
    run_p.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to execute")
    run_p.add_argument("--timeout", type=float, default=None)

    # list
    list_p = subparsers.add_parser("list", help="List recorded job runs")
    list_p.add_argument("--status", choices=["success", "failure", "running"])
    list_p.add_argument("--job", dest="job_name")
    list_p.add_argument("--since", help="ISO datetime string")

    add_export_subparser(subparsers)
    add_stats_subparser(subparsers)
    add_notify_subparser(subparsers)
    add_retention_subparser(subparsers)
    add_tags_subparser(subparsers)
    add_alerts_subparser(subparsers)
    add_schedule_subparser(subparsers)
    add_hooks_subparser(subparsers)
    add_annotations_subparser(subparsers)
    add_dependencies_subparser(subparsers)

    return parser


def cmd_run(args, storage: JobRunStorage) -> None:
    if not args.cmd:
        print("Error: no command provided.", file=sys.stderr)
        sys.exit(1)
    run = run_job(
        job_name=args.job_name,
        command=args.cmd,
        storage=storage,
        timeout=args.timeout,
    )
    status = run.status.value if hasattr(run.status, "value") else run.status
    print(f"[{status.upper()}] {args.job_name} (exit {run.exit_code})")


def cmd_list(args, storage: JobRunStorage) -> None:
    runs = storage.load_all()
    if args.status:
        runs = filter_by_status(runs, args.status)
    if getattr(args, "job_name", None):
        runs = filter_by_job_name(runs, args.job_name)
    if getattr(args, "since", None):
        from datetime import datetime
        since_dt = datetime.fromisoformat(args.since)
        runs = filter_since(runs, since_dt)
    print(format_run_table(runs))


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    storage = JobRunStorage(log_dir=args.log_dir)

    dispatch = {
        "run": cmd_run,
        "list": cmd_list,
        "export": cmd_export,
        "stats": cmd_stats,
        "notify": cmd_notify,
        "prune": cmd_prune,
        "tags": cmd_tags,
        "alerts": cmd_alerts,
        "schedule": cmd_schedule,
        "hooks": cmd_hooks,
        "annotations": cmd_annotations,
        "deps": cmd_deps,
    }

    handler = dispatch.get(args.command)
    if handler is None:
        parser.print_help()
        return
    handler(args, storage)


if __name__ == "__main__":
    main()
