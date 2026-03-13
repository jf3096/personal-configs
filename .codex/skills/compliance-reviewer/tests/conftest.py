from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest

GLOBAL_HOOK = Path('/home/jf3096/.codex/hooks/pre-completion-check.sh')
SKILL_HOOK = Path('/home/jf3096/.codex/skills/compliance-reviewer/hooks/pre-completion-check.sh')


@dataclass
class HookResult:
    exit_code: int
    stdout: str
    stderr: str


@pytest.fixture(scope='session')
def global_hook_path() -> Path:
    assert GLOBAL_HOOK.exists(), f'missing hook: {GLOBAL_HOOK}'
    return GLOBAL_HOOK


@pytest.fixture(scope='session')
def skill_hook_path() -> Path:
    assert SKILL_HOOK.exists(), f'missing hook: {SKILL_HOOK}'
    return SKILL_HOOK


def compliance_receipt_block(exit_code: int = 0, verdict: str = 'PASS') -> str:
    return (
        'Compliance Skill: $compliance-reviewer\n'
        'Hook Command: cat /tmp/response-draft.txt | COMPLIANCE_REVIEW_VERBOSE=true bash /home/jf3096/.codex/skills/compliance-reviewer/hooks/pre-completion-check.sh\n'
        f'Hook Exit: {exit_code}\n'
        f'Hook Verdict: {verdict}\n'
    )


def verdict_block(
    *,
    compliance_verdict: str = 'PASS',
    delivery_verdict: str = 'PASS',
    release_advice: str = 'Ship',
) -> str:
    return (
        f'Compliance Verdict: {compliance_verdict}\n'
        f'Delivery Verdict: {delivery_verdict}\n'
        f'Release Advice: {release_advice}\n'
    )


def high_risk_block(*, files_changed: int = 6, line_delta: int = 201) -> str:
    return (
        'High Risk Assessment\n'
        '- high_risk: true\n'
        f'- files_changed: {files_changed}\n'
        f'- line_delta: {line_delta}\n'
    )


def tdd_revalidation_block(
    *,
    command: str = 'python3 -c "import json; print(json.dumps({'
    '\'revalidation_status\': \'pass\', \'test_evidence\': [\'t1\'], \'run_evidence\': [\'r1\']}))"',
) -> str:
    return (
        'TDD-Strict Revalidation\n'
        f'TDD Revalidation Command: {command}\n'
    )


def stage2_recommendation_block() -> str:
    return (
        'Stage 2 推荐门禁上下文摘要\n'
        '- task_goal: 为 compliance-reviewer 增加双阶段推荐门禁 MVP\n'
        '- change_objects: skill, validator_script\n'
        '- change_summary: 增加 Stage 2 契约和推荐门禁生成器\n'
        '- executed_commands: pytest targeted suite\n'
        '- existing_evidence: targeted tests passed\n'
        '- risk_points: Stage 2 仍为可开关契约\n'
        'Stage 2 推荐门禁清单\n'
        '- change_type: skill\n'
        '- change_summary: 新增推荐门禁 MVP\n'
        '- impact_scope: cross-task\n'
        '- recommended_checks: positive_case, negative_case, adversarial_case\n'
        '- reason: 修改了复用契约和推荐逻辑\n'
        '- severity: suggest_blocking\n'
        '- requires_user_confirmation: true\n'
    )


def stage2_executable_recheck_block(
    *,
    command: str = 'python3 -c "print(\'json-ok\')"',
    expect_exit: int = 0,
    expect_stdout: str | None = 'json-ok',
    expect_stderr: str | None = None,
) -> str:
    lines = [
        'Stage 2 可执行复验命令',
        f'- run: {command}',
        f'- expect_exit: {expect_exit}',
    ]
    if expect_stdout is not None:
        lines.append(f'- expect_stdout: {expect_stdout}')
    if expect_stderr is not None:
        lines.append(f'- expect_stderr: {expect_stderr}')
    return '\n'.join(lines) + '\n'


def run_hook(input_text: str, hook_path: Path, env: dict[str, str] | None = None) -> HookResult:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    proc = subprocess.run(
        ['bash', str(hook_path)],
        input=input_text,
        text=True,
        capture_output=True,
        env=merged_env,
        check=False,
    )
    return HookResult(exit_code=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
