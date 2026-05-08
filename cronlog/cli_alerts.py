"""CLI subcommand for managing and testing alert rules."""

import argparse
from cronlog.alerts import (
    evaluate_rules,
    failure_alert_rule,
    long_running_alert_rule,
    register_rule,
    unregister_all,
)
from cronlog.storage import JobRunStorage
from cronlog.query import JobRunQuery


def add_alerts_subparser(subparsers: argparse._SubParsersAction) -> None:
    parser = subparsers.add_parser("alerts", help="Evaluate alert rules against stored runs")
    parser.add_argument("--log-dir", default=".cronlog", help="Log directory")
    parser.add_argument(
        "--failure", action="store_true", help="Alert on any failed run"
    )
    parser.add_argument(
        "--job", default=None, metavar="NAME", help="Scope alerts to a specific job name"
    )
    parser.add_argument(
        "--long-running",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Alert on runs exceeding this duration in seconds",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=None,
        metavar="N",
        help="Only evaluate the last N runs",
    )
    parser.set_defaults(func=cmd_alerts)


def cmd_alerts(args: argparse.Namespace) -> None:
    rules = []

    if args.failure:
        rules.append(failure_alert_rule(job_name=args.job))

    if args.long_running is not None:
        rules.append(long_running_alert_rule(args.long_running, job_name=args.job))

    if not rules:
        print("No alert rules specified. Use --failure or --long-running.")
        return

    storage = JobRunStorage(args.log_dir)
    query = JobRunQuery(storage)
    runs = query.all()

    if args.last is not None:
        runs = runs[-args.last:]

    triggered_total = 0
    for run in runs:
        messages = evaluate_rules(run, rules=rules)
        for msg in messages:
            print(msg)
            triggered_total += 1

    if triggered_total == 0:
        print("No alerts triggered.")
    else:
        print(f"\n{triggered_total} alert(s) triggered.")
