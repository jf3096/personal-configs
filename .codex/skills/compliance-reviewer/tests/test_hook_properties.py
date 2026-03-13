from __future__ import annotations

import pytest

from conftest import compliance_receipt_block, run_hook, verdict_block


@pytest.mark.parametrize(
    'body',
    [
        '进度更新：今天补了注释。\n',
        'chore: rename local variable\n',
        '说明：仅讨论方案，不是完成声明。\n',
    ],
)
def test_p1_non_claim_text_does_not_require_status(body: str, global_hook_path) -> None:
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 0


@pytest.mark.parametrize(
    'status_line',
    [
        '状态：修改（未验证：等待测试环境就绪）\n',
        '状态: 修改(未验证: CI 暂不可用)\n',
        '修改（未验证：权限限制）\n',
    ],
)
def test_p2_unverified_branch_passes_without_positive_evidence(status_line: str, global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + verdict_block(delivery_verdict='BLOCKED', release_advice='Hold')
        + '说明：暂时无法验证。\n'
        + status_line
    )
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 0


@pytest.mark.parametrize(
    'word',
    [
        'should work',
        'probably',
        'theoretically',
        '预期',
        '理论上',
        '应该可以',
    ],
)
def test_p3_speculative_words_fail_verified_branch(word: str, global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + verdict_block()
        + f'验证：test passed\n结论：{word}\n状态：完成（已验证：pytest -q）\n'
    )
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1


def test_p4_last_non_empty_line_controls_status_evaluation(global_hook_path) -> None:
    base = compliance_receipt_block() + verdict_block() + '任务已完成。\n状态：完成（已验证：test passed）\n'
    pass_case = base + '\n\n'
    fail_case = base + '附加说明\n'

    result_pass = run_hook(pass_case, global_hook_path)
    result_fail = run_hook(fail_case, global_hook_path)

    assert result_pass.exit_code == 0
    assert result_fail.exit_code == 1
    assert 'Missing standardized final status line' in (result_fail.stdout + result_fail.stderr)
