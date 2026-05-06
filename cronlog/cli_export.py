"""CLI subcommand for exporting job run data."""

import sys
from argparse import ArgumentParser, Namespace
from typing import Optional

from cronlog.export import export_runs
from cronlog.query import JobRunQuery
from cronlog.storage import JobRunStorage


def add_export_subparser(subparsers) -> None:
    """Register the 'export' subcommand on an existing subparsers action."""
    parser: ArgumentParser = subparsers.add_parser(
        "export",
        help="Export job run history to JSON or CSV",
    )
    parser.add_argument(
        "--format",
        choices=["json", "csv"],
        default="json",
        dest="fmt",
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--job",
        metavar="NAME",
        default=None,
        help="Filter by job name",
    )
    parser.add_argument(
        "--status",
        choices=["success", "failure"],
        default=None,
        help="Filter by job status",
    )
    parser.add_argument(
        "--output",
        metavar="FILE",
        default=None,
        help="Write output to FILE instead of stdout",
    )
    parser.set_defaults(func=cmd_export)


def cmd_export(args: Namespace, storage: Optional[JobRunStorage] = None) -> int:
    """Handle the 'export' subcommand. Returns an exit code."""
    if storage is None:
        storage = JobRunStorage()

    query = JobRunQuery(storage)

    if args.job:
        query = query.for_job(args.job)
    if args.status == "failure":
        query = query.failures()
    elif args.status == "success":
        query = query.successes()

    runs = query.all()

    try:
        output = export_runs(runs, args.fmt)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(output)
    else:
        print(output)

    return 0
