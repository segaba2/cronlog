"""CLI subcommands for tag management."""

import argparse
from cronlog.storage import JobRunStorage
from cronlog.tags import add_tag, remove_tag, filter_by_tag, all_tags


def add_tags_subparser(subparsers) -> None:
    parser = subparsers.add_parser("tags", help="Manage tags on job runs")
    tag_sub = parser.add_subparsers(dest="tag_cmd", required=True)

    # cronlog tags add <run_id> <tag>
    p_add = tag_sub.add_parser("add", help="Add a tag to a run")
    p_add.add_argument("run_id", help="Run ID to tag")
    p_add.add_argument("tag", help="Tag to attach")

    # cronlog tags remove <run_id> <tag>
    p_rm = tag_sub.add_parser("remove", help="Remove a tag from a run")
    p_rm.add_argument("run_id", help="Run ID")
    p_rm.add_argument("tag", help="Tag to remove")

    # cronlog tags list
    tag_sub.add_parser("list", help="List all tags across all runs")

    # cronlog tags filter <tag>
    p_filter = tag_sub.add_parser("filter", help="Show runs with a given tag")
    p_filter.add_argument("tag", help="Tag to filter by")

    parser.set_defaults(func=cmd_tags)


def cmd_tags(args: argparse.Namespace, storage: JobRunStorage) -> None:
    runs = storage.load_all()

    if args.tag_cmd == "add":
        matched = [r for r in runs if r.run_id == args.run_id]
        if not matched:
            print(f"Error: run '{args.run_id}' not found.")
            return
        run = add_tag(matched[0], args.tag)
        storage.save(run)
        print(f"Tag '{args.tag}' added to run {run.run_id}.")

    elif args.tag_cmd == "remove":
        matched = [r for r in runs if r.run_id == args.run_id]
        if not matched:
            print(f"Error: run '{args.run_id}' not found.")
            return
        run = remove_tag(matched[0], args.tag)
        storage.save(run)
        print(f"Tag '{args.tag}' removed from run {run.run_id}.")

    elif args.tag_cmd == "list":
        tags = all_tags(runs)
        if not tags:
            print("No tags found.")
        else:
            for tag in tags:
                print(tag)

    elif args.tag_cmd == "filter":
        results = filter_by_tag(runs, args.tag)
        if not results:
            print(f"No runs found with tag '{args.tag}'.")
        else:
            for r in results:
                tags_str = ", ".join(r.tags)
                print(f"{r.run_id}  {r.job_name}  [{tags_str}]")
