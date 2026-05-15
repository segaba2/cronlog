"""CLI sub-command: cronlog score — display health scores for job runs."""

from __future__ import annotations

import argparse
import json

from cronlog.scoring import score_by_job, score_runs
from cronlog.storage import JobRunStorage


def add_scoring_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("score", help="Show health scores for job runs")
    parser.add_argument("--job", metavar="NAME", help="Filter to a specific job name")
    parser.add_argument(
        "--baseline",
        type=float,
        default=0.0,
        metavar="SECONDS",
        help="Expected duration in seconds used for duration scoring (default: 0)",
    )
    parser.add_argument(
        "--by-job",
        action="store_true",
        help="Aggregate scores per job rather than listing individual runs",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="as_json",
        help="Output as JSON",
    )
    parser.add_argument("--log-dir", default=".cronlog", help="Log directory")
    parser.set_defaults(func=cmd_score)


def cmd_score(args: argparse.Namespace) -> None:
    storage = JobRunStorage(args.log_dir)
    runs = storage.load_all()

    if getattr(args, "job", None):
        runs = [r for r in runs if r.job_name == args.job]

    baseline = getattr(args, "baseline", 0.0)

    if args.by_job:
        result = score_by_job(runs, baseline_seconds=baseline)
        if args.as_json:
            print(json.dumps(result, indent=2))
        else:
            if not result:
                print("No runs found.")
                return
            print(f"{'Job':<30} {'Avg Score':>10}")
            print("-" * 42)
            for job, avg in sorted(result.items(), key=lambda kv: -kv[1]):
                print(f"{job:<30} {avg:>10.2f}")
    else:
        scored = score_runs(runs, baseline_seconds=baseline)
        if args.as_json:
            print(json.dumps(scored, indent=2))
        else:
            if not scored:
                print("No runs found.")
                return
            print(f"{'Run ID':<36} {'Job':<25} {'Score':>8}")
            print("-" * 72)
            for entry in scored:
                print(
                    f"{entry['run_id']:<36} {entry['job_name']:<25} {entry['score']:>8.2f}"
                )
