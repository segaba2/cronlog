"""Main CLI entry point for cronlog."""

from __future__ import annotations

import argparse
import sys

from cronlog.runner import run_job
from cronlog.storage import JobRunStorage
from cronlog.formatter import format_run_table, format_run_detail
from cronlog.query import JobRunQuery
from cronlog.cli_export import add_export_subparser
from cronlog.cli_stats import add_stats_subparser
from cronlog.cli_notify import add_notify_subparser
from cronlog.cli_retention import add_retention_subparser
from cronlog.cli_alerts import add_alerts_subparser
from cronlog.cli_schedule import add_schedule_subparser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronlog",
        description="Lightweight cron job output capture and query tool.",
    )
    parser.add_argument("--log-dir", default=".cronlog", help="Directory for log storage")
    subparsers = parser.add_subparsers(dest="cmd")

    # run
    p_run = subparsers.add_parser("run", help="Run a command and capture its output")
    p_run.add_argument("job_name", help="Logical name for this job")
    p_run.add_argument("command", nargs=argparse.REMAINDER, help="Command to execute")
    p_run.set_defaults(func=cmd_run)

    # list
    p_list = subparsers.add_parser("list", help="List recorded job runs")
    p_list.add_argument("--job", help="Filter by job name")
    p_list.add_argument("--status", choices=["success", "failure", "running"])
    p_list.add_argument("--detail", action="store_true", help="Show full detail for each run")
    p_list.set_defaults(func=cmd_list)

    add_export_subparser(subparsers)
    add_stats_subparser(subparsers)
    add_notify_subparser(subparsers)
    add_retention_subparser(subparsers)
    add_alerts_subparser(subparsers)
    add_schedule_subparser(subparsers)

    return parser


def cmd_run(args: argparse.Namespace) -> None:
    storage = JobRunStorage(log_dir=args.log_dir)
    command = " ".join(args.command)
    run_job(job_name=args.job_name, command=command, storage=storage)


def cmd_list(args: argparse.Namespace) -> None:
    storage = JobRunStorage(log_dir=args.log_dir)
    query = JobRunQuery(storage)

    runs = query.all()
    if args.job:
        runs = query.for_job(args.job)
    if args.status == "success":
        runs = [r for r in runs if r.status.value == "success"]
    elif args.status == "failure":
        runs = [r for r in runs if r.status.value == "failure"]
    elif args.status == "running":
        runs = [r for r in runs if r.status.value == "running"]

    if not runs:
        print("No runs found.")
        return

    if args.detail:
        for run in runs:
            print(format_run_detail(run))
    else:
        print(format_run_table(runs))


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
