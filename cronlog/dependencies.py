"""Job dependency tracking for cronlog.

Allows jobs to declare that they must run after other jobs succeed.
"""

from __future__ import annotations

from typing import Dict, List, Optional

_dependencies: Dict[str, List[str]] = {}


def register_dependency(job_name: str, depends_on: str) -> None:
    """Register that *job_name* depends on *depends_on* completing successfully."""
    if not job_name or not depends_on:
        return
    job_name = job_name.strip().lower()
    depends_on = depends_on.strip().lower()
    if job_name == depends_on:
        raise ValueError(f"Job '{job_name}' cannot depend on itself.")
    _dependencies.setdefault(job_name, [])
    if depends_on not in _dependencies[job_name]:
        _dependencies[job_name].append(depends_on)


def unregister_dependency(job_name: str, depends_on: str) -> None:
    """Remove a single dependency edge."""
    job_name = job_name.strip().lower()
    depends_on = depends_on.strip().lower()
    deps = _dependencies.get(job_name, [])
    _dependencies[job_name] = [d for d in deps if d != depends_on]


def unregister_all() -> None:
    """Clear all registered dependencies (useful in tests)."""
    _dependencies.clear()


def get_dependencies(job_name: str) -> List[str]:
    """Return the list of jobs that *job_name* depends on."""
    return list(_dependencies.get(job_name.strip().lower(), []))


def all_dependencies() -> Dict[str, List[str]]:
    """Return a copy of the full dependency map."""
    return {k: list(v) for k, v in _dependencies.items()}


def is_satisfied(job_name: str, runs) -> bool:
    """Return True if all dependencies of *job_name* have a recent successful run.

    *runs* should be an iterable of JobRun-like dicts (as returned by to_dict)
    or JobRun objects with .job_name and .status attributes.
    """
    deps = get_dependencies(job_name)
    if not deps:
        return True

    succeeded: set = set()
    for run in runs:
        if isinstance(run, dict):
            name = run.get("job_name", "")
            status = run.get("status", "")
        else:
            name = getattr(run, "job_name", "")
            status = getattr(run, "status", "")
        if hasattr(status, "value"):
            status = status.value
        if status == "success":
            succeeded.add(name.lower())

    return all(dep in succeeded for dep in deps)


def detect_cycles() -> Optional[List[str]]:
    """Return a cycle path if one exists, otherwise None."""
    visited: set = set()
    path: List[str] = []

    def dfs(node: str) -> Optional[List[str]]:
        if node in path:
            cycle_start = path.index(node)
            return path[cycle_start:] + [node]
        if node in visited:
            return None
        visited.add(node)
        path.append(node)
        for dep in _dependencies.get(node, []):
            result = dfs(dep)
            if result:
                return result
        path.pop()
        return None

    for job in list(_dependencies.keys()):
        result = dfs(job)
        if result:
            return result
    return None
