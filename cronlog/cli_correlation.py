"""CLI subcommands for inspecting run correlations."""

from __future__ import annotations

import argparse
import json
import sys

from cronlog.correlation import get_correlated_ids, find_correlated_runs, all_correlation_ids
from cronlog.storage import JobRunStorage


def add_correlation_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser(
        "correlation",
        help="Inspect correlated job runs",
    )
    sub = parser.add_subparsers(dest="correlation_cmd", required=True)

    # list all correlation IDs
    sub.add_parser("ids", help="List all known correlation IDs")

    # show runs for a correlation ID
    show = sub.add_parser("show", help="Show runs linked to a correlation ID")
    show.add_argument("correlation_id", help="Correlation ID to look up")
    show.add_argument("--json", dest="as_json", action="store_true", help="Output as JSON")
    show.add_argument("--log-dir", default=".cronlog", help="Log directory")

    parser.set_defaults(func=cmd_correlation)


def cmd_correlation(args: argparse.Namespace) -> None:
    if args.correlation_cmd == "ids":
        ids = all_correlation_ids()
        if not ids:
            print("No correlation IDs recorded.")
        else:
            for cid in sorted(ids):
                print(cid)
        return

    if args.correlation_cmd == "show":
        storage = JobRunStorage(log_dir=args.log_dir)
        all_runs = storage.load_all()
        correlated = find_correlated_runs(args.correlation_id, all_runs)
        linked_ids = get_correlated_ids(args.correlation_id)

        if not linked_ids:
            print(f"No runs found for correlation ID '{args.correlation_id}'.")
            sys.exit(1)

        if args.as_json:
            data = [r.to_dict() for r in correlated]
            print(json.dumps(data, indent=2, default=str))
        else:
            if not correlated:
                print(f"Correlation ID '{args.correlation_id}' has {len(linked_ids)} run ID(s) but none are in storage.")
                for rid in linked_ids:
                    print(f"  {rid}")
            else:
                print(f"Runs for correlation ID '{args.correlation_id}':")
                for run in correlated:
                    status = getattr(run, 'status', 'unknown')
                    print(f"  [{status}] {run.job_name}  id={run.run_id}")
