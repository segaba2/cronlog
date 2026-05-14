"""CLI subcommand for ranking job runs."""

from __future__ import annotations

import argparse

from cronlog.ranking import (
    rank_by_duration,
    rank_by_failure_rate,
    rank_by_run_count,
    top_n,
)
from cronlog.storage import JobRunStorage


def add_ranking_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("rank", help="Rank job runs by various criteria")
    parser.add_argument(
        "criterion",
        choices=["duration", "failure-rate", "run-count"],
        help="Ranking criterion",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        metavar="N",
        help="Show top N results (default: 10)",
    )
    parser.add_argument(
        "--asc",
        action="store_true",
        help="Sort ascending instead of descending",
    )
    parser.add_argument("--log-dir", default=".cronlog", help="Log directory")
    parser.set_defaults(func=cmd_rank)


def cmd_rank(args: argparse.Namespace) -> None:
    storage = JobRunStorage(args.log_dir)
    runs = storage.load_all()

    if not runs:
        print("No runs found.")
        return

    criterion = args.criterion
    n = args.top

    if criterion == "duration":
        ranked = rank_by_duration(runs, descending=not args.asc)
        results = top_n(ranked, n)
        print(f"{'Rank':<6} {'Job':<30} {'Duration (s)':<14} {'Run ID'}")
        print("-" * 70)
        for rank, run in results:
            from cronlog.ranking import _duration_seconds
            dur = _duration_seconds(run)
            print(f"{rank:<6} {run.job_name:<30} {dur:<14.2f} {run.run_id}")

    elif criterion == "failure-rate":
        ranked = rank_by_failure_rate(runs)
        results = top_n(ranked, n)
        print(f"{'Rank':<6} {'Job':<30} {'Failure Rate':<14} {'Total Runs'}")
        print("-" * 65)
        for i, (name, rate, total) in enumerate(results, start=1):
            print(f"{i:<6} {name:<30} {rate * 100:<13.1f}% {total}")

    elif criterion == "run-count":
        ranked = rank_by_run_count(runs)
        if args.asc:
            ranked = list(reversed(ranked))
        results = top_n(ranked, n)
        print(f"{'Rank':<6} {'Job':<30} {'Run Count'}")
        print("-" * 50)
        for i, (name, count) in enumerate(results, start=1):
            print(f"{i:<6} {name:<30} {count}")
