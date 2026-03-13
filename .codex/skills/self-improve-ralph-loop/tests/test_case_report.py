from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def _message(report_body: str) -> str:
    return f"<case_report>\n{report_body.strip()}\n</case_report>\n"


def _load_module():
    module_path = Path(__file__).resolve().parents[1] / "scripts" / "ralph_loop.py"
    spec = importlib.util.spec_from_file_location("ralph_loop_module", module_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_validate_case_report_positive_pass(tmp_path: Path) -> None:
    ralph_loop = _load_module()

    evidence = tmp_path / "evidence.txt"
    evidence.write_text("ok\n", encoding="utf-8")
    message = _message(
        f"""
case_id: case-positive
verdict: pass
expectation_check: met
failure_signal_check: not_hit
evidence_refs: {evidence}
confidence: 95
next_action: stop
"""
    )

    report = ralph_loop.parse_case_report(message)
    verdict, issues = ralph_loop.validate_case_result(
        report=report,
        case_type="positive",
        workspace=tmp_path,
    )
    assert verdict is True
    assert issues == []


def test_validate_case_report_negative_requires_failure_signal_hit(tmp_path: Path) -> None:
    ralph_loop = _load_module()

    evidence = tmp_path / "evidence.txt"
    evidence.write_text("ok\n", encoding="utf-8")
    message = _message(
        f"""
case_id: case-negative
verdict: pass
expectation_check: met
failure_signal_check: not_hit
evidence_refs: {evidence}
confidence: 88
next_action: continue
"""
    )
    report = ralph_loop.parse_case_report(message)
    verdict, issues = ralph_loop.validate_case_result(
        report=report,
        case_type="negative",
        workspace=tmp_path,
    )
    assert verdict is False
    assert "negative_case_requires_failure_hit" in issues


def test_validate_case_report_fails_when_evidence_missing(tmp_path: Path) -> None:
    ralph_loop = _load_module()

    missing = tmp_path / "missing.txt"
    message = _message(
        f"""
case_id: case-positive
verdict: pass
expectation_check: met
failure_signal_check: not_hit
evidence_refs: {missing}
confidence: 80
next_action: retry
"""
    )
    report = ralph_loop.parse_case_report(message)
    verdict, issues = ralph_loop.validate_case_result(
        report=report,
        case_type="positive",
        workspace=tmp_path,
    )
    assert verdict is False
    assert "evidence_missing" in issues
