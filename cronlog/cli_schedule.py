"""CLI subcommands for managing scheduled job definitions."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone

from cronlog.schedule import ScheduledJob, ScheduleStore


def add_schedule_subparser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("schedule", help="Manage scheduled job definitions")
    sub = p.add_subparsers(dest="schedule_cmd", required=True)

    # --- add ---
    p_add = sub.add_parser("add", help="Register a new scheduled job")
    p_add.add_argument("name", help="Unique job name")
    p_add.add_argument("command", help="Shell command to run")
    p_add.add_argument("cron_expr", help="Cron expression, e.g. '0 2 * * *'")
    p_add.add_argument("--tag", dest="tags", action="append", default=[], metavar="TAG")
    p_add.add_argument("--description", default="")
    p_add.add_argument("--schedules-file", default="schedules.json")

    # --- remove ---
    p_rm = sub.add_parser("remove", help="Remove a scheduled job")
    p_rm.add_argument("name")
    p_rm.add_argument("--schedules-file", default="schedules.json")

    # --- list ---
    p_ls = sub.add_parser("list", help="List all scheduled jobs")
    p_ls.add_argument("--schedules-file", default="schedules.json")

    # --- next ---
    p_nx = sub.add_parser("next", help="Show next run time for a job")
    p_nx.add_argument("name")
    p_nx.add_argument("--schedules-file", default="schedules.json")

    p.set_defaults(func=cmd_schedule)


def cmd_schedule(args: argparse.Namespace) -> None:
    store = ScheduleStore(path=args.schedules_file)

    if args.schedule_cmd == "add":
        job = ScheduledJob(
            name=args.name,
            command=args.command,
            cron_expr=args.cron_expr,
            tags=args.tags,
            description=args.description,
        )
        try:
            store.add(job)
            print(f"Scheduled job '{args.name}' added.")
        except ValueError as exc:
            print(f"Error: {exc}")

    elif args.schedule_cmd == "remove":
        if store.remove(args.name):
            print(f"Scheduled job '{args.name}' removed.")
        else:
            print(f"No scheduled job named '{args.name}' found.")

    elif args.schedule_cmd == "list":
        jobs = store.all()
        if not jobs:
            print("No scheduled jobs defined.")
            return
        for job in jobs:
            status = "enabled" if job.enabled else "disabled"
            print(f"  {job.name:<20} {job.cron_expr:<15} {status:<10} {job.command}")

    elif args.schedule_cmd == "next":
        job = store.get(args.name)
        if job is None:
            print(f"No scheduled job named '{args.name}' found.")
            return
        nxt = job.next_run(datetime.now(timezone.utc))
        print(f"Next run for '{args.name}': {nxt.isoformat()}")
