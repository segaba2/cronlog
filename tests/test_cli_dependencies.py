"""Tests for cronlog.cli_dependencies."""

import argparse
import pytest
from unittest.mock import MagicMock

import cronlog.dependencies as dep_module
from cronlog.cli_dependencies import add_dependencies_subparser, cmd_deps


@pytest.fixture(autouse=True)
def clean_deps():
    dep_module.unregister_all()
    yield
    dep_module.unregister_all()


def make_args(**kwargs):
    base = {"deps_cmd": None}
    base.update(kwargs)
    ns = argparse.Namespace(**base)
    return ns


@pytest.fixture
def storage():
    mock = MagicMock()
    mock.load_all.return_value = []
    return mock


def test_add_dependencies_subparser_registers_deps(storage):
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    add_dependencies_subparser(sub)
    args = parser.parse_args(["deps", "list"])
    assert args.cmd == "deps"


def test_cmd_add_registers_dependency(storage, capsys):
    args = make_args(deps_cmd="add", job="b", depends_on="a")
    cmd_deps(args, storage)
    assert "a" in dep_module.get_dependencies("b")
    out = capsys.readouterr().out
    assert "added" in out


def test_cmd_add_self_dependency_prints_error(storage, capsys):
    args = make_args(deps_cmd="add", job="a", depends_on="a")
    cmd_deps(args, storage)
    out = capsys.readouterr().out
    assert "Error" in out


def test_cmd_remove_removes_dependency(storage, capsys):
    dep_module.register_dependency("b", "a")
    args = make_args(deps_cmd="remove", job="b", depends_on="a")
    cmd_deps(args, storage)
    assert "a" not in dep_module.get_dependencies("b")


def test_cmd_list_empty(storage, capsys):
    args = make_args(deps_cmd="list")
    cmd_deps(args, storage)
    out = capsys.readouterr().out
    assert "No dependencies" in out


def test_cmd_list_shows_edges(storage, capsys):
    dep_module.register_dependency("b", "a")
    args = make_args(deps_cmd="list")
    cmd_deps(args, storage)
    out = capsys.readouterr().out
    assert "b" in out and "a" in out


def test_cmd_check_satisfied(storage, capsys):
    dep_module.register_dependency("b", "a")
    storage.load_all.return_value = [{"job_name": "a", "status": "success"}]
    args = make_args(deps_cmd="check", job="b")
    cmd_deps(args, storage)
    out = capsys.readouterr().out
    assert "satisfied" in out
    assert "NOT" not in out


def test_cmd_check_not_satisfied(storage, capsys):
    dep_module.register_dependency("b", "a")
    storage.load_all.return_value = []
    args = make_args(deps_cmd="check", job="b")
    cmd_deps(args, storage)
    out = capsys.readouterr().out
    assert "NOT satisfied" in out


def test_cmd_cycles_none(storage, capsys):
    args = make_args(deps_cmd="cycles")
    cmd_deps(args, storage)
    out = capsys.readouterr().out
    assert "No cycles" in out


def test_cmd_cycles_detected(storage, capsys):
    dep_module.register_dependency("a", "b")
    dep_module.register_dependency("b", "a")
    args = make_args(deps_cmd="cycles")
    cmd_deps(args, storage)
    out = capsys.readouterr().out
    assert "Cycle detected" in out


def test_cmd_no_subcommand_prints_usage(storage, capsys):
    args = make_args(deps_cmd=None)
    cmd_deps(args, storage)
    out = capsys.readouterr().out
    assert "Usage" in out
