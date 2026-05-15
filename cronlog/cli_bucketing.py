"""CLI sub-command for time-bucket analysis of job runs."""

from __future__ import annotations

import argparse
import json
from typing import List

from cronlog.bucketing import (
    bucket_by_day,
    bucket_by_hour,
    bucket_by_minute_interval,
    bucket_run_counts,
)
from cronlog.models import JobRun
from cronlog.storage import JobRunStorage


def add_bucketing_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser(
        "bucket",
        help="Aggregate job runs into time buckets",
    )
    parser.add_argument(
        "--mode",
        choices=["hour", "day", "interval"],
        default="hour",
        help="Bucketing granularity (default: hour)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        metavar="MINUTES",
        help="Bucket width in minutes when --mode=interval (default: 5)",
    )
    parser.add_argument(
        "--job",
        metavar="NAME",
        help="Filter to a specific job name",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON",
    )
    parser.set_defaults(func=cmd_bucket)


def cmd_bucket(args: argparse.Namespace, storage: JobRunStorage) -> None:
    runs: List[JobRun] = storage.load_all()

    if args.job:
        runs = [r for r in runs if r.job_name == args.job]

    if not runs:
        print("No runs found.")
        return

    if args.mode == "day":
        buckets = bucket_by_day(runs)
    elif args.mode == "interval":
        buckets = bucket_by_minute_interval(runs, args.interval)
    else:
        buckets = bucket_by_hour(runs)

    counts = bucket_run_counts(buckets)

    if args.json:
        print(json.dumps(counts, indent=2))
        return

    col_w = max((len(k) for k in counts), default=10)
    print(f"{'Bucket':<{col_w}}  {'Count':>6}")
    print("-" * (col_w + 9))
    for key, count in counts.items():
        print(f"{key:<{col_w}}  {count:>6}")
