from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "ralph_loop.py"
    spec = importlib.util.spec_from_file_location("ralph_loop_module", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_load_todo_plan_applies_defaults_for_positive_case(tmp_path: Path) -> None:
    ralph_loop = _load_module()

    cases_root = tmp_path / "cases"
    _write(
        cases_root / "catalog.yaml",
        """
version: 1
suite_name: sample
cases:
  - id: case-positive
    title: positive case
    type: positive
    priority: high
    spec_file: case-positive.md
    enabled: true
""".strip()
        + "\n",
    )
    _write(cases_root / "case-positive.md", "# Case: case-positive\n")

    todo_file = tmp_path / "todo.yaml"
    _write(
        todo_file,
        """
todo_id: demo
loop_rounds: 2
items:
  - case_id: case-positive
""".strip()
        + "\n",
    )

    catalog = ralph_loop.load_catalog(cases_root)
    todo = ralph_loop.load_todo_plan(todo_file, catalog)

    assert todo["continue_on_failure"] is True
    assert todo["selection_policy"] == "highest_priority_pending"
    assert todo["completion_policy"]["mode"] == "all_enabled_cases_passed"
    assert todo["items"][0]["enabled"] is True
    assert todo["items"][0]["stability_runs"] == 3
    assert todo["items"][0]["stability_pass_threshold"] == 3


def test_load_todo_plan_rejects_unknown_case_id(tmp_path: Path) -> None:
    ralph_loop = _load_module()

    cases_root = tmp_path / "cases"
    _write(
        cases_root / "catalog.yaml",
        """
version: 1
suite_name: sample
cases:
  - id: known-case
    title: known
    type: positive
    spec_file: known.md
""".strip()
        + "\n",
    )
    _write(cases_root / "known.md", "# Case: known-case\n")

    todo_file = tmp_path / "todo.yaml"
    _write(
        todo_file,
        """
todo_id: demo
loop_rounds: 1
items:
  - case_id: unknown-case
""".strip()
        + "\n",
    )

    catalog = ralph_loop.load_catalog(cases_root)
    with pytest.raises(ValueError, match="unknown case_id"):
        ralph_loop.load_todo_plan(todo_file, catalog)


def test_load_catalog_requires_id(tmp_path: Path) -> None:
    ralph_loop = _load_module()

    cases_root = tmp_path / "cases"
    _write(
        cases_root / "catalog.yaml",
        """
version: 1
suite_name: bad
cases:
  - title: missing id
    type: positive
    spec_file: missing.md
""".strip()
        + "\n",
    )
    _write(cases_root / "missing.md", "# Case: missing\n")

    with pytest.raises(ValueError, match="missing required field: id"):
        ralph_loop.load_catalog(cases_root)
