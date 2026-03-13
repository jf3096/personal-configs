from __future__ import annotations

import pytest

from conftest import compliance_receipt_block, run_hook, stage2_executable_recheck_block


@pytest.mark.parametrize(
    'name,body,expected_exit,expected_stderr',
    [
        (
            'A_progress_only',
            '这里是进度更新，不是完成结论。\n',
            0,
            '',
        ),
        (
            'B_claim_done_no_status',
            '这个任务已完成。\n验证：测试通过。\n',
            1,
            'Missing standardized final status line',
        ),
        (
            'C_status_verified_only',
            compliance_receipt_block() + '状态：完成（已验证：pytest -q 全部通过）\n',
            0,
            '',
        ),
        (
            'D_status_unverified_with_reason',
            compliance_receipt_block() + '受环境限制无法联网下载依赖。\n状态：修改（未验证：网络隔离，无法拉取包）\n',
            0,
            '',
        ),
        (
            'E_speculative_language',
            compliance_receipt_block() + '本次改动 should work。\n状态：完成（已验证：pytest -q）\n',
            1,
            'Completion/modification claim without sufficient verification evidence',
        ),
        (
            'F_stage2_structured_recommendation_section',
            compliance_receipt_block()
            + 'Stage 2 推荐门禁上下文摘要\n'
            + '- task_goal: 调整 compliance-reviewer 的双阶段文档\n'
            + '- change_objects: skill\n'
            + '- change_summary: 增加 Stage 2 契约说明\n'
            + '- executed_commands: rg -n "Stage 2" ...\n'
            + '- existing_evidence: 文档 diff 已检查\n'
            + '- risk_points: 文档与实现可能不一致\n'
            + 'Stage 2 推荐门禁清单\n'
            + '- change_type: skill\n'
            + '- change_summary: 更新 skill 文档\n'
            + '- impact_scope: local\n'
            + '- recommended_checks: positive_case, negative_case\n'
            + '- reason: 敏感类型但仅局部影响\n'
            + '- severity: strongly_suggested\n'
            + '- requires_user_confirmation: true\n'
            + stage2_executable_recheck_block(
                command='python3 -c "print(\'stage2-ok\')"',
                expect_stdout='stage2-ok',
            )
            + '验证通过：rg -n "Stage 2" /home/jf3096/.codex/skills/compliance-reviewer/SKILL.md\n'
            + '状态：修改（已验证：rg -n "Stage 2" /home/jf3096/.codex/skills/compliance-reviewer/SKILL.md 命中 3 处）\n',
            0,
            '',
        ),
        (
            'G_env_sensitive_fixture_only_claim',
            compliance_receipt_block()
            + '本次修改涉及真实路径挂载和真实 session 数据。\n'
            + '验证：node --test tests/codex-sess.test.js 全部通过\n'
            + '状态：修改（已验证：node --test tests/codex-sess.test.js exit 0）\n',
            1,
            'real-environment verification evidence',
        ),
        (
            'H_env_sensitive_real_data_verified',
            compliance_receipt_block()
            + '本次修改涉及真实路径挂载和真实 session 数据。\n'
            + '运行结果：使用真实 ~/.codex/sessions 数据执行展示检查，确认出现 js/poc-design2 分组。\n'
            + '状态：修改（已验证：node display-check.js exit 0；real session data verified）\n',
            0,
            '',
        ),
        (
            'I_env_sensitive_adversarial_wording',
            compliance_receipt_block()
            + '本次修改涉及真实路径挂载和真实 session 数据。\n'
            + '验证：基于真实场景模拟 fixture 数据的 node --test 全部通过\n'
            + '状态：修改（已验证：node --test tests/codex-sess.test.js exit 0）\n',
            1,
            'real-environment verification evidence',
        ),
    ],
)
def test_example_matrix(name: str, body: str, expected_exit: int, expected_stderr: str, global_hook_path) -> None:
    result = run_hook(body, global_hook_path)
    assert result.exit_code == expected_exit, f'case={name} stderr={result.stderr} stdout={result.stdout}'
    if expected_stderr:
        assert expected_stderr in (result.stdout + result.stderr)


def test_verbose_probe(global_hook_path) -> None:
    body = compliance_receipt_block() + '状态：完成（已验证：pytest -q 全部通过）\n'
    result = run_hook(body, global_hook_path, env={'COMPLIANCE_REVIEW_VERBOSE': 'true'})
    assert result.exit_code == 0
    assert '[compliance-hook]' in result.stderr
    assert 'has_status=true' in result.stderr
