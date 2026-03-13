from __future__ import annotations

import pytest

from conftest import compliance_receipt_block, run_hook, verdict_block


def test_adversarial_case_insensitive_completion_keyword(global_hook_path) -> None:
    body = 'Task COMPLETED successfully.\n验证：test passed\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1
    assert 'Missing standardized final status line' in (result.stdout + result.stderr)


def test_adversarial_fullwidth_punctuation_status(global_hook_path) -> None:
    body = compliance_receipt_block() + verdict_block() + '状态：完成（已验证：test passed）\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 0


def test_adversarial_multiple_status_lines_only_last_effective(global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + verdict_block(delivery_verdict='BLOCKED', release_advice='Hold')
        + '状态：完成（已验证：test passed）\n任务已完成\n状态：修改（未验证：等待环境）\n'
    )
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 0


def test_adversarial_obfuscated_evidence_keyword_fails(global_hook_path) -> None:
    # Full-width 'ｅ' breaks literal keyword match for 'test passed'.
    body = compliance_receipt_block() + verdict_block() + '说明：tｅst passed\n状态：完成（已验证：pytest）\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1


@pytest.mark.xfail(reason='当前实现为关键词匹配，代码块内关键字会被计入证据，属于已知局限')
def test_adversarial_keyword_in_codeblock_should_not_count_as_evidence(global_hook_path) -> None:
    body = compliance_receipt_block() + verdict_block() + '```text\n' 'test passed\n' '```\n' '状态：完成（已验证：pytest）\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1


@pytest.mark.xfail(reason='当前实现为字符串匹配，URL 中的 modified 可能触发声明判定，属于已知局限')
def test_adversarial_url_keyword_should_not_trigger_claim(global_hook_path) -> None:
    body = 'https://example.com/docs/modified?from=changelog\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 0


def test_adversarial_stage2_fields_outside_sections_do_not_count(global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + verdict_block()
        + 'Stage 2 推荐门禁上下文摘要\n'
        + '这里只写一句摘要，没有字段。\n'
        + 'Stage 2 推荐门禁清单\n'
        + '这里只写一句说明，没有字段。\n'
        + '附录\n'
        + '- task_goal: 漂移到错误区域\n'
        + '- change_type: skill\n'
        + '- change_summary: 漂移字段\n'
        + '- impact_scope: cross-task\n'
        + '- recommended_checks: positive_case, negative_case\n'
        + '- reason: 这些字段不应被 Stage 2 检查计入\n'
        + '- severity: suggest_blocking\n'
        + '- requires_user_confirmation: true\n'
        + '验证：test passed\n'
        + '状态：完成（已验证：pytest -q test passed）\n'
    )
    result = run_hook(body, global_hook_path, env={'COMPLIANCE_REVIEW_REQUIRE_STAGE2': 'true'})
    assert result.exit_code == 1
    assert 'Incomplete Stage 2 recommendation structure' in (result.stdout + result.stderr)
