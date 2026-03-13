from __future__ import annotations

import json
import subprocess
from pathlib import Path


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _script_path() -> Path:
    return Path(__file__).resolve().parents[1] / "scripts" / "ralph_loop.py"


def test_todo_start_status_cancel_resume_dry_run(tmp_path: Path) -> None:
    script = _script_path()
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    cases_root = workspace / "cases"
    _write(
        cases_root / "catalog.yaml",
        """
version: 1
suite_name: smoke
cases:
  - id: case-positive
    title: positive
    type: positive
    priority: high
    spec_file: case-positive.md
    enabled: true
""".strip()
        + "\n",
    )
    _write(cases_root / "case-positive.md", "# Case: case-positive\n")
    todo_file = workspace / "todo.yaml"
    _write(
        todo_file,
        """
todo_id: smoke
loop_rounds: 1
items:
  - case_id: case-positive
""".strip()
        + "\n",
    )
    run_root = workspace / "runs"

    start = subprocess.run(
        [
            "python3",
            str(script),
            "todo-start",
            "--workspace",
            str(workspace),
            "--cases-root",
            str(cases_root),
            "--todo-file",
            str(todo_file),
            "--run-root",
            str(run_root),
            "--dry-run",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert start.returncode == 0, start.stderr
    run_dir = Path(start.stdout.strip())
    assert run_dir.exists()
    assert (run_dir / "state.json").exists()
    assert (run_dir / "todo.snapshot.yaml").exists()
    assert (run_dir / "scoreboard.json").exists()
    assert (run_dir / "progress.txt").exists()

    status = subprocess.run(
        ["python3", str(script), "todo-status", str(run_dir), "--json"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert status.returncode == 0, status.stderr
    payload = json.loads(status.stdout)
    assert payload["todo_id"] == "smoke"

    cancel = subprocess.run(
        ["python3", str(script), "todo-cancel", str(run_dir)],
        check=False,
        capture_output=True,
        text=True,
    )
    assert cancel.returncode == 0, cancel.stderr
    assert (run_dir / "cancel.request").exists()

    resume = subprocess.run(
        ["python3", str(script), "todo-resume", str(run_dir), "--dry-run", "--force"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert resume.returncode == 0, resume.stderr
