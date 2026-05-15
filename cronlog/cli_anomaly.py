"""CLI subcommand for anomaly detection."""

from __future__ import annotations

import argparse

from cronlog.anomaly import anomaly_report, detect_duration_anomalies, detect_failure_bursts
from cronlog.storage import JobRunStorage


def add_anomaly_subparser(subparsers) -> None:
    parser = subparsers.add_parser("anomaly", help="Detect anomalous job runs")
    parser.add_argument("--log-dir", default="logs", help="Log directory")
    parser.add_argument(
        "--mode",
        choices=["duration", "bursts", "all"],
        default="all",
        help="Anomaly detection mode",
    )
    parser.add_argument(
        "--z-threshold",
        type=float,
        default=2.0,
        help="Z-score threshold for duration anomalies",
    )
    parser.add_argument(
        "--job",
        default=None,
        help="Filter to a specific job name",
    )
    parser.set_defaults(func=cmd_anomaly)


def cmd_anomaly(args: argparse.Namespace) -> None:
    storage = JobRunStorage(args.log_dir)
    runs = storage.load_all()

    if args.job:
        runs = [r for r in runs if r.job_name == args.job]

    if not runs:
        print("No runs found.")
        return

    if args.mode == "duration":
        anomalies = detect_duration_anomalies(runs, args.z_threshold)
        _print_anomaly_table("Duration Anomalies", anomalies)
    elif args.mode == "bursts":
        bursts = detect_failure_bursts(runs)
        _print_anomaly_table("Failure Bursts", bursts)
    else:
        report = anomaly_report(runs, args.z_threshold)
        _print_anomaly_table("Duration Anomalies", report["duration_anomalies"])
        _print_anomaly_table("Failure Bursts", report["failure_bursts"])
        print(f"Total unique anomalous runs: {report['total_anomalies']}")


def _print_anomaly_table(title: str, runs) -> None:
    print(f"\n{title} ({len(runs)} found):")
    if not runs:
        print("  (none)")
        return
    print(f"  {'ID':<36}  {'Job':<20}  {'Status':<10}  {'Started At'}")
    print("  " + "-" * 76)
    for run in runs:
        started = str(run.started_at)[:19] if run.started_at else "N/A"
        print(f"  {run.run_id:<36}  {run.job_name:<20}  {run.status.value:<10}  {started}")
