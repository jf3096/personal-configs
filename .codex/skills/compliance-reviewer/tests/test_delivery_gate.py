from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SCRIPT_PATH = Path('/home/jf3096/.codex/skills/compliance-reviewer/scripts/delivery_gate.py')


def load_module():
    spec = spec_from_file_location('delivery_gate', SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_requires_dual_verdict_fields() -> None:
    module = load_module()
    ok, message = module.evaluate_delivery_contract('状态：完成（已验证：pytest -q）\n')
    assert ok is False
    assert 'Compliance Verdict' in message


def test_high_risk_cannot_use_plain_pass() -> None:
    module = load_module()
    text = (
        'Compliance Verdict: PASS\n'
        'Delivery Verdict: PASS\n'
        'Release Advice: Ship\n'
        '- high_risk: true\n'
    )
    ok, message = module.evaluate_delivery_contract(text)
    assert ok is False
    assert 'cannot declare Delivery Verdict PASS' in message


def test_pass_with_high_risk_requires_tdd_command() -> None:
    module = load_module()
    text = (
        'Compliance Verdict: PASS\n'
        'Delivery Verdict: PASS_WITH_HIGH_RISK\n'
        'Release Advice: Hold\n'
        '- high_risk: true\n'
    )
    ok, message = module.evaluate_delivery_contract(text)
    assert ok is False
    assert 'requires TDD-Strict Revalidation command' in message


def test_high_risk_blocked_accepts_tdd_cli_failure() -> None:
    module = load_module()
    text = (
        'Compliance Verdict: PASS\n'
        'Delivery Verdict: BLOCKED\n'
        'Release Advice: Hold\n'
        '- high_risk: true\n'
        'TDD-Strict Revalidation\n'
        'TDD Revalidation Command: python3 -c "import sys; sys.exit(2)"\n'
    )
    ok, message = module.evaluate_delivery_contract(text)
    assert ok is True
    assert message == ''


def test_high_risk_pass_with_high_risk_requires_pass_json() -> None:
    module = load_module()
    text = (
        'Compliance Verdict: PASS\n'
        'Delivery Verdict: PASS_WITH_HIGH_RISK\n'
        'Release Advice: Hold\n'
        '- high_risk: true\n'
        'command: pytest -q\n'
        'result: exit 0\n'
        'TDD-Strict Revalidation\n'
        'TDD Revalidation Command: python3 -c "import json; print(json.dumps({'
        '\'revalidation_status\': \'pass\', \'test_evidence\': [\'t1\'], \'run_evidence\': [\'r1\']}))"\n'
    )
    ok, message = module.evaluate_delivery_contract(text)
    assert ok is True
    assert message == ''


def test_executable_claim_requires_runtime_evidence() -> None:
    module = load_module()
    text = (
        'Compliance Verdict: PASS\n'
        'Delivery Verdict: PASS\n'
        'Release Advice: Ship\n'
        '本次可以 start server。\n'
    )
    ok, message = module.evaluate_delivery_contract(text)
    assert ok is False
    assert 'Executable claim requires runtime evidence' in message
