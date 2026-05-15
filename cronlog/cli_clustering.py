"""CLI subcommand for clustering job runs."""

from __future__ import annotations

import argparse
import json

from cronlog.clustering import (
    cluster_by_duration_bucket,
    cluster_by_job_and_status,
    cluster_by_outcome,
)
from cronlog.storage import JobRunStorage


def add_clustering_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("cluster", help="Cluster job runs by similarity")
    parser.add_argument(
        "--mode",
        choices=["duration", "outcome", "job-status"],
        default="outcome",
        help="Clustering mode (default: outcome)",
    )
    parser.add_argument(
        "--bucket-size",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Bucket size in seconds for duration mode (default: 60)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="output_json",
        help="Output cluster sizes as JSON",
    )
    parser.add_argument("--log-dir", default=".cronlog", help="Log directory")
    parser.set_defaults(func=cmd_cluster)


def cmd_cluster(args: argparse.Namespace) -> None:
    storage = JobRunStorage(args.log_dir)
    runs = storage.load_all()

    if not runs:
        print("No runs found.")
        return

    if args.mode == "duration":
        clusters = cluster_by_duration_bucket(runs, bucket_size=args.bucket_size)
    elif args.mode == "outcome":
        clusters = cluster_by_outcome(runs)
    else:
        clusters = cluster_by_job_and_status(runs)

    if args.output_json:
        summary = {k: len(v) for k, v in sorted(clusters.items())}
        print(json.dumps(summary, indent=2))
        return

    print(f"{'Cluster':<40} {'Count':>6}")
    print("-" * 48)
    for key in sorted(clusters.keys()):
        count = len(clusters[key])
        print(f"{key:<40} {count:>6}")
