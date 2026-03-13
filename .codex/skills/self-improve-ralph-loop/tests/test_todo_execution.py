from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "ralph_loop.py"
    spec = importlib.util.spec_from_file_location("ralph_loop_module_exec", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _build_state(tmp_path: Path) -> tuple[dict, dict]:
    state = {
        "version": 1,
        "mode": "todo",
        "status": "running",
        "started_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
        "workspace": str(tmp_path),
        "run_dir": str(tmp_path / "run"),
        "todo_file": str(tmp_path / "todo.yaml"),
        "cases_root": str(tmp_path / "cases"),
        "catalog_file": str(tmp_path / "cases" / "catalog.yaml"),
        "todo_id": "demo",
        "loop_rounds": 3,
        "current_round": 0,
        "continue_on_failure": True,
        "selection_policy": "highest_priority_pending",
        "completion_policy": {"mode": "all_enabled_cases_passed", "completion_promise": "DONE"},
        "items": [
            {
                "case_id": "case-positive",
                "enabled": True,
                "priority": "high",
                "type": "positive",
                "spec_path": str(tmp_path / "cases" / "case-positive.md"),
                "quality_checks": [],
                "stability_runs": 3,
                "stability_pass_threshold": 3,
                "max_attempts": 0,
            }
        ],
        "model": None,
        "sandbox": "workspace-write",
        "skip_git_repo_check": False,
        "codex_args": [],
        "dry_run": False,
        "last_stop_reason": None,
        "exit_reason": None,
    }
    scoreboard = {
        "version": 1,
        "cases": {
            "case-positive": {
                "case_id": "case-positive",
                "type": "positive",
                "priority": "high",
                "enabled": True,
                "status": "pending",
                "attempts": 0,
                "passes": 0,
                "fails": 0,
                "stability_runs": 3,
                "stability_pass_threshold": 3,
                "last_issues": [],
                "history": [],
            }
        },
    }
    return state, scoreboard


def test_run_todo_loop_completes_when_3_of_3_pass(tmp_path: Path) -> None:
    ralph_loop = _load_module()
    run_dir = tmp_path / "run"
    files = ralph_loop.build_todo_run_files(run_dir)
    ralph_loop.ensure_dir(files.run_dir)
    ralph_loop.ensure_dir(files.items_dir)
    (tmp_path / "cases").mkdir(parents=True, exist_ok=True)
    (tmp_path / "cases" / "case-positive.md").write_text("# Case\n", encoding="utf-8")
    state, scoreboard = _build_state(tmp_path)

    def _fake_run_case_attempt(**kwargs):
        attempt_dir = kwargs["attempt_dir"]
        ralph_loop.ensure_dir(attempt_dir)
        (attempt_dir / "report.md").write_text("ok\n", encoding="utf-8")
        (attempt_dir / "stdout.log").write_text("ok\n", encoding="utf-8")
        (attempt_dir / "stderr.log").write_text("", encoding="utf-8")
        return {
            "passed": True,
            "issues": [],
            "exit_code": 0,
            "report_file": str(attempt_dir / "report.md"),
            "stdout_file": str(attempt_dir / "stdout.log"),
            "stderr_file": str(attempt_dir / "stderr.log"),
        }

    ralph_loop.run_case_attempt = _fake_run_case_attempt
    exit_code = ralph_loop.run_todo_loop(files, state, scoreboard, dry_run=False)
    assert exit_code == 0
    assert state["status"] == "completed"
    assert scoreboard["cases"]["case-positive"]["status"] == "passed"
    assert scoreboard["cases"]["case-positive"]["attempts"] == 3


def test_run_todo_loop_hits_max_rounds_when_not_stable(tmp_path: Path) -> None:
    ralph_loop = _load_module()
    run_dir = tmp_path / "run"
    files = ralph_loop.build_todo_run_files(run_dir)
    ralph_loop.ensure_dir(files.run_dir)
    ralph_loop.ensure_dir(files.items_dir)
    (tmp_path / "cases").mkdir(parents=True, exist_ok=True)
    (tmp_path / "cases" / "case-positive.md").write_text("# Case\n", encoding="utf-8")
    state, scoreboard = _build_state(tmp_path)
    outcomes = iter([True, False, True])

    def _fake_run_case_attempt(**kwargs):
        attempt_dir = kwargs["attempt_dir"]
        ralph_loop.ensure_dir(attempt_dir)
        (attempt_dir / "report.md").write_text("ok\n", encoding="utf-8")
        (attempt_dir / "stdout.log").write_text("ok\n", encoding="utf-8")
        (attempt_dir / "stderr.log").write_text("", encoding="utf-8")
        return {
            "passed": next(outcomes),
            "issues": [],
            "exit_code": 0,
            "report_file": str(attempt_dir / "report.md"),
            "stdout_file": str(attempt_dir / "stdout.log"),
            "stderr_file": str(attempt_dir / "stderr.log"),
        }

    ralph_loop.run_case_attempt = _fake_run_case_attempt
    exit_code = ralph_loop.run_todo_loop(files, state, scoreboard, dry_run=False)
    assert exit_code == 0
    assert state["status"] == "max_rounds_reached"
    assert scoreboard["cases"]["case-positive"]["status"] == "pending"
