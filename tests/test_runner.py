import sys
import pytest

from cronlog.models import JobStatus
from cronlog.runner import run_job
from cronlog.storage import JobRunStorage


@pytest.fixture
def storage(tmp_path):
    return JobRunStorage(log_dir=tmp_path)


def test_successful_command_sets_success_status():
    run = run_job("echo_job", [sys.executable, "-c", "print('hello')"])
    assert run.status == JobStatus.SUCCESS
    assert run.exit_code == 0


def test_stdout_is_captured():
    run = run_job("echo_job", [sys.executable, "-c", "print('hello world')"])
    assert "hello world" in run.stdout


def test_stderr_is_captured():
    run = run_job(
        "err_job",
        [sys.executable, "-c", "import sys; sys.stderr.write('oops\\n')"],
    )
    assert any("oops" in line for line in run.stderr)


def test_failing_command_sets_failure_status():
    run = run_job("fail_job", [sys.executable, "-c", "raise SystemExit(1)"])
    assert run.status == JobStatus.FAILURE
    assert run.exit_code == 1


def test_missing_command_sets_failure_status():
    run = run_job("bad_job", ["__nonexistent_binary__"])
    assert run.status == JobStatus.FAILURE
    assert run.exit_code == 127


def test_run_is_saved_when_storage_provided(storage):
    run = run_job("save_job", [sys.executable, "-c", "pass"], storage=storage)
    runs = storage.load_all()
    assert len(runs) == 1
    assert runs[0].run_id == run.run_id


def test_run_is_not_saved_without_storage():
    # Should not raise even without storage
    run = run_job("no_storage_job", [sys.executable, "-c", "pass"])
    assert run.status == JobStatus.SUCCESS


def test_timeout_sets_failure_status():
    run = run_job(
        "timeout_job",
        [sys.executable, "-c", "import time; time.sleep(10)"],
        timeout=1,
    )
    assert run.status == JobStatus.FAILURE
    assert run.exit_code == -1
    assert any("timed out" in line for line in run.stderr)
