"""CLI sub-command for the heatmap feature."""

from __future__ import annotations

import argparse
import json

from cronlog.heatmap import (
    format_heatmap,
    heatmap_by_day,
    heatmap_by_hour,
    heatmap_by_weekday_hour,
)
from cronlog.storage import JobRunStorage


def add_heatmap_subparser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    parser = subparsers.add_parser("heatmap", help="Show run-frequency heatmaps")
    parser.add_argument(
        "--mode",
        choices=["hour", "day", "weekday-hour"],
        default="hour",
        help="Aggregation mode (default: hour)",
    )
    parser.add_argument(
        "--job", metavar="NAME", help="Filter to a specific job name"
    )
    parser.add_argument(
        "--top", type=int, default=10, metavar="N", help="Show top N buckets"
    )
    parser.add_argument(
        "--json", action="store_true", dest="as_json", help="Output as JSON"
    )
    parser.add_argument(
        "--log-dir", default=".cronlog", metavar="DIR", help="Log directory"
    )
    parser.set_defaults(func=cmd_heatmap)


def cmd_heatmap(args: argparse.Namespace) -> None:
    storage = JobRunStorage(args.log_dir)
    runs = storage.load_all()

    if args.job:
        runs = [r for r in runs if r.job_name == args.job]

    if not runs:
        print("No runs found.")
        return

    if args.mode == "hour":
        data = heatmap_by_hour(runs)
    elif args.mode == "day":
        data = heatmap_by_day(runs)
    else:
        raw = heatmap_by_weekday_hour(runs)
        data = {f"{wd},{hr}": cnt for (wd, hr), cnt in raw.items()}

    if args.as_json:
        print(json.dumps(data, sort_keys=True))
    else:
        print(format_heatmap(data, top_n=args.top))
