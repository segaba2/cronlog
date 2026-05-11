"""Tests for cronlog.replay."""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from cronlog.models import JobRun, JobStatus
from cronlog.replay import find_run, replay_run


def _make_finished_run(run_id: str = "abc-123", job_name: str = "nightly") -> JobRun:
    run = JobRun(job_name=job_name, command="echo hello")
    run.run_id = run_id
    run.finish(exit_code=0, stdout="hello", stderr="")
    return run


@pytest.fixture()
def storage():
    store = MagicMock()
    store.load_all.return_value = [_make_finished_run("id-1"), _make_finished_run("id-2", "daily")]
    return store


# ---------------------------------------------------------------------------
# find_run
# ---------------------------------------------------------------------------

def test_find_run_returns_matching_run(storage):
    result = find_run(storage, "id-1")
    assert result is not None
    assert result.run_id == "id-1"


def test_find_run_returns_none_for_unknown_id(storage):
    result = find_run(storage, "does-not-exist")
    assert result is None


def test_find_run_returns_correct_job_name(storage):
    result = find_run(storage, "id-2")
    assert result.job_name == "daily"


# ---------------------------------------------------------------------------
# replay_run
# ---------------------------------------------------------------------------

def test_replay_run_raises_for_unknown_id(storage):
    with pytest.raises(ValueError, match="No run found"):
        replay_run(storage, "nonexistent")


def test_replay_run_calls_run_job_with_original_details(storage):
    new_run = _make_finished_run("new-id", "nightly")
    with patch("cronlog.replay.run_job", return_value=new_run) as mock_run_job:
        result = replay_run(storage, "id-1")
        mock_run_job.assert_called_once_with(
            job_name="nightly",
            command="echo hello",
            storage=storage,
            timeout=None,
        )
    assert result is new_run


def test_replay_run_passes_timeout(storage):
    new_run = _make_finished_run("new-id")
    with patch("cronlog.replay.run_job", return_value=new_run) as mock_run_job:
        replay_run(storage, "id-1", timeout=30.0)
        _, kwargs = mock_run_job.call_args
        assert kwargs["timeout"] == 30.0


def test_replay_run_returns_new_run_not_original(storage):
    original = find_run(storage, "id-1")
    new_run = _make_finished_run("brand-new-id")
    with patch("cronlog.replay.run_job", return_value=new_run):
        result = replay_run(storage, "id-1")
    assert result.run_id != original.run_id
