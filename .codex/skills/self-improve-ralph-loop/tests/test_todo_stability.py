from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "ralph_loop.py"
    spec = importlib.util.spec_from_file_location("ralph_loop_module_stability", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_compute_stability_pass_for_positive_3_of_3() -> None:
    ralph_loop = _load_module()
    status = ralph_loop.compute_stability_status(
        case_type="positive",
        recent_results=[True, True, True],
        stability_runs=3,
        stability_pass_threshold=3,
    )
    assert status == "passed"


def test_compute_stability_pending_for_positive_2_of_3() -> None:
    ralph_loop = _load_module()
    status = ralph_loop.compute_stability_status(
        case_type="positive",
        recent_results=[True, False, True],
        stability_runs=3,
        stability_pass_threshold=3,
    )
    assert status == "pending"


def test_run_quality_checks_fails_on_nonzero_exit(tmp_path: Path) -> None:
    ralph_loop = _load_module()
    logs_dir = tmp_path / "logs"
    ok, results = ralph_loop.run_quality_checks(
        commands=["true", "false"],
        workspace=tmp_path,
        logs_dir=logs_dir,
    )
    assert ok is False
    assert len(results) == 2
    assert results[1]["exit_code"] != 0
    assert (logs_dir / "quality-check-002.stdout.log").exists()
    assert (logs_dir / "quality-check-002.stderr.log").exists()


def test_select_next_case_prefers_high_priority_pending() -> None:
    ralph_loop = _load_module()
    items = [
        {"case_id": "case-medium", "enabled": True, "priority": "medium"},
        {"case_id": "case-high", "enabled": True, "priority": "high"},
    ]
    scoreboard = {
        "cases": {
            "case-medium": {"status": "pending"},
            "case-high": {"status": "pending"},
        }
    }
    selected = ralph_loop.select_next_case(items, scoreboard, "highest_priority_pending")
    assert selected is not None
    assert selected["case_id"] == "case-high"
