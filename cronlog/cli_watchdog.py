"""CLI sub-command: watchdog — report overdue scheduled jobs."""

from __future__ import annotations

import argparse
import json

from cronlog.storage import JobRunStorage
from cronlog.watchdog import watchdog_report


def add_watchdog_subparser(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    p = subparsers.add_parser(
        "watchdog",
        help="Report scheduled jobs that appear to be overdue.",
    )
    p.add_argument(
        "--grace",
        type=int,
        default=300,
        metavar="SECONDS",
        help="Grace period in seconds after scheduled time (default: 300).",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output results as JSON.",
    )
    p.add_argument(
        "--log-dir",
        default=".cronlog",
        help="Directory used by cronlog for storage (default: .cronlog).",
    )
    p.set_defaults(func=cmd_watchdog)


def cmd_watchdog(args: argparse.Namespace) -> None:
    storage = JobRunStorage(args.log_dir)
    overdue = watchdog_report(storage, args.log_dir, grace_seconds=args.grace)

    if not overdue:
        print("All scheduled jobs are on time.")
        return

    if args.as_json:
        print(json.dumps(overdue, indent=2))
        return

    print(f"{'JOB NAME':<30} {'CRON':<20} {'LAST DUE'}")
    print("-" * 70)
    for entry in overdue:
        print(
            f"{entry['job_name']:<30} {entry['cron']:<20} {entry['last_due']}"
        )
