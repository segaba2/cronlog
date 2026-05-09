"""CLI subcommands for managing job dependencies."""

from __future__ import annotations

import argparse

import cronlog.dependencies as dep_module


def add_dependencies_subparser(subparsers) -> None:
    parser = subparsers.add_parser("deps", help="Manage job dependencies")
    sub = parser.add_subparsers(dest="deps_cmd")

    # add
    add_p = sub.add_parser("add", help="Add a dependency edge")
    add_p.add_argument("job", help="Job that depends on another")
    add_p.add_argument("depends_on", help="Job that must succeed first")

    # remove
    rm_p = sub.add_parser("remove", help="Remove a dependency edge")
    rm_p.add_argument("job")
    rm_p.add_argument("depends_on")

    # list
    sub.add_parser("list", help="List all dependencies")

    # check
    check_p = sub.add_parser("check", help="Check if dependencies are satisfied")
    check_p.add_argument("job", help="Job name to check")

    # cycles
    sub.add_parser("cycles", help="Detect dependency cycles")

    parser.set_defaults(func=cmd_deps)


def cmd_deps(args, storage) -> None:
    cmd = getattr(args, "deps_cmd", None)

    if cmd == "add":
        try:
            dep_module.register_dependency(args.job, args.depends_on)
            print(f"Dependency added: '{args.job}' depends on '{args.depends_on}'.")
        except ValueError as exc:
            print(f"Error: {exc}")

    elif cmd == "remove":
        dep_module.unregister_dependency(args.job, args.depends_on)
        print(f"Dependency removed: '{args.job}' no longer depends on '{args.depends_on}'.")

    elif cmd == "list":
        all_deps = dep_module.all_dependencies()
        if not all_deps:
            print("No dependencies registered.")
            return
        for job, predecessors in sorted(all_deps.items()):
            for pred in predecessors:
                print(f"  {job}  ->  {pred}")

    elif cmd == "check":
        runs = storage.load_all()
        satisfied = dep_module.is_satisfied(args.job, runs)
        status = "satisfied" if satisfied else "NOT satisfied"
        print(f"Dependencies for '{args.job}': {status}")

    elif cmd == "cycles":
        cycle = dep_module.detect_cycles()
        if cycle:
            print("Cycle detected: " + " -> ".join(cycle))
        else:
            print("No cycles detected.")

    else:
        print("Usage: cronlog deps {add,remove,list,check,cycles}")
