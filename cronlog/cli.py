"""Main CLI entry point for cronlog."""

from __future__ import annotations

import argparse
import sys

from cronlog.storage import JobRunStorage
from cronlog.runner import run_job
from cronlog.formatter import format_run_table, format_run_detail
from cronlog.filters import (
    filter_by_status,
    filter_by_job_name,
    filter_since,
    filter_until,
    sort_by_started_at,
)
from cronlog.cli_export import add_export_subparser
from cronlog.cli_stats import add_stats_subparser
from cronlog.cli_notify import add_notify_subparser
from cronlog.cli_retention import add_retention_subparser
from cronlog.cli_tags import add_tags_subparser
from cronlog.cli_alerts import add_alerts_subparser
from cronlog.cli_schedule import add_schedule_subparser
from cronlog.cli_hooks import add_hooks_subparser
from cronlog.cli_annotations import add_annotations_subparser
from cronlog.cli_dependencies import add_dependencies_subparser
from cronlog.cli_replay import add_replay_subparser
from cronlog.cli_audit import add_audit_subparser
from cronlog.cli_watchdog import add_watchdog_subparser
from cronlog.cli_snapshots import add_snapshots_subparser
from cronlog.cli_correlation import add_correlation_subparser
from cronlog.cli_pipeline import add_pipeline_subparser
from cronlog.cli_profiler import add_profiler_subparser
from cronlog.cli_baseline import add_baseline_subparser
from cronlog.cli_ranking import add_ranking_subparser
from cronlog.cli_scoring import add_scoring_subparser
from cronlog.cli_heatmap import add_heatmap_subparser
from cronlog.cli_anomaly import add_anomaly_subparser
from cronlog.cli_clustering import add_clustering_subparser
from cronlog.cli_labeling import add_labeling_subparser
from cronlog.cli_bucketing import add_bucketing_subparser


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cronlog",
        description="Lightweight cron job output capture and query tool",
    )
    parser.add_argument(
        "--log-dir",
        default=".cronlog",
        help="Directory for log storage (default: .cronlog)",
    )
    subparsers = parser.add_subparsers(dest="command")

    # run
    run_parser = subparsers.add_parser("run", help="Execute a command and log its output")
    run_parser.add_argument("job_name", help="Name for this job")
    run_parser.add_argument("cmd", nargs=argparse.REMAINDER, help="Command to run")
    run_parser.set_defaults(func=cmd_run)

    # list
    list_parser = subparsers.add_parser("list", help="List recorded job runs")
    list_parser.add_argument("--job", metavar="NAME", help="Filter by job name")
    list_parser.add_argument("--status", choices=["success", "failure", "running"], help="Filter by status")
    list_parser.add_argument("--since", metavar="ISO_DATETIME", help="Show runs after this time")
    list_parser.add_argument("--until", metavar="ISO_DATETIME", help="Show runs before this time")
    list_parser.add_argument("--detail", metavar="RUN_ID", help="Show full detail for a run ID")
    list_parser.set_defaults(func=cmd_list)

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
    add_replay_subparser(subparsers)
    add_audit_subparser(subparsers)
    add_watchdog_subparser(subparsers)
    add_snapshots_subparser(subparsers)
    add_correlation_subparser(subparsers)
    add_pipeline_subparser(subparsers)
    add_profiler_subparser(subparsers)
    add_baseline_subparser(subparsers)
    add_ranking_subparser(subparsers)
    add_scoring_subparser(subparsers)
    add_heatmap_subparser(subparsers)
    add_anomaly_subparser(subparsers)
    add_clustering_subparser(subparsers)
    add_labeling_subparser(subparsers)
    add_bucketing_subparser(subparsers)

    return parser


def cmd_run(args: argparse.Namespace, storage: JobRunStorage) -> None:
    if not args.cmd:
        print("Error: no command specified.", file=sys.stderr)
        sys.exit(1)
    run_job(args.job_name, args.cmd, storage)


def cmd_list(args: argparse.Namespace, storage: JobRunStorage) -> None:
    runs = storage.load_all()

    if args.detail:
        matched = [r for r in runs if r.run_id == args.detail]
        if not matched:
            print(f"No run found with id {args.detail}", file=sys.stderr)
            sys.exit(1)
        print(format_run_detail(matched[0]))
        return

    if args.job:
        runs = filter_by_job_name(runs, args.job)
    if args.status:
        runs = filter_by_status(runs, args.status)
    if args.since:
        from datetime import datetime, timezone
        since_dt = datetime.fromisoformat(args.since).replace(tzinfo=timezone.utc)
        runs = filter_since(runs, since_dt)
    if args.until:
        from datetime import datetime, timezone
        until_dt = datetime.fromisoformat(args.until).replace(tzinfo=timezone.utc)
        runs = filter_until(runs, until_dt)

    runs = sort_by_started_at(runs)
    print(format_run_table(runs))


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    storage = JobRunStorage(log_dir=args.log_dir)
    args.func(args, storage)


if __name__ == "__main__":
    main()
