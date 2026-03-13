from __future__ import annotations

from conftest import (
    compliance_receipt_block,
    run_hook,
    stage2_executable_recheck_block,
    stage2_recommendation_block,
)


def test_r1_requires_standard_status_when_claiming_completion(global_hook_path) -> None:
    body = '任务完成，已交付。\n验证：测试通过。\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1
    assert 'Missing standardized final status line' in (result.stdout + result.stderr)


def test_r2_requires_evidence_in_verified_branch(global_hook_path) -> None:
    body = compliance_receipt_block() + '状态：完成（已验证：）\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1
    assert (
        'Completion/modification claim has empty verification payload' in (result.stdout + result.stderr)
        or 'Completion/modification claim without sufficient verification evidence' in (result.stdout + result.stderr)
    )


def test_r3_blocks_speculative_language(global_hook_path) -> None:
    body = compliance_receipt_block() + '验证：test passed\n理论上没有问题\n状态：完成（已验证：pytest -q）\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1


def test_r4_allows_unverified_with_reason(global_hook_path) -> None:
    body = compliance_receipt_block() + '依赖源不可访问。\n状态：修改（未验证：网络策略阻断依赖下载）\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 0


def test_r5_only_last_non_empty_line_is_status(global_hook_path) -> None:
    body = compliance_receipt_block() + '任务已完成。\n状态：完成（已验证：pytest -q）\n补充说明：后续继续观察。\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1
    assert 'Missing standardized final status line' in (result.stdout + result.stderr)


def test_r6_bypass_short_circuits_all_checks(global_hook_path) -> None:
    body = '任务已完成 should work\n没有状态行也没有证据\n'
    result = run_hook(body, global_hook_path, env={'COMPLIANCE_REVIEW_BYPASS_HOOK': '1'})
    assert result.exit_code == 0


def test_r7_verbose_prints_decision_fields(global_hook_path) -> None:
    body = compliance_receipt_block() + '状态：完成（已验证：test passed）\n'
    result = run_hook(body, global_hook_path, env={'COMPLIANCE_REVIEW_VERBOSE': 'true'})
    assert result.exit_code == 0
    assert 'claims_completion=' in result.stderr
    assert 'has_status=' in result.stderr
    assert 'has_compliance_receipt=' in result.stderr


def test_r8_require_standard_status_toggle(global_hook_path) -> None:
    body = compliance_receipt_block() + '任务已完成。\n验证：测试通过。\n'
    strict_result = run_hook(body, global_hook_path)
    relaxed_result = run_hook(body, global_hook_path, env={'COMPLIANCE_REVIEW_REQUIRE_STANDARD_STATUS': 'false'})

    assert strict_result.exit_code == 1
    assert relaxed_result.exit_code == 0


def test_r9_requires_compliance_receipt(global_hook_path) -> None:
    body = '验证：test passed\n状态：完成（已验证：pytest -q）\n'
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1
    assert 'Missing compliance-reviewer receipt block' in (result.stdout + result.stderr)


def test_r10_stage2_not_required_when_toggle_disabled(global_hook_path) -> None:
    body = compliance_receipt_block() + '验证：test passed\n状态：完成（已验证：pytest -q test passed）\n'
    result = run_hook(body, global_hook_path, env={'COMPLIANCE_REVIEW_REQUIRE_STAGE2': 'false'})
    assert result.exit_code == 0


def test_r11_stage2_required_when_toggle_enabled(global_hook_path) -> None:
    body = compliance_receipt_block() + '验证：test passed\n状态：完成（已验证：pytest -q test passed）\n'
    result = run_hook(body, global_hook_path, env={'COMPLIANCE_REVIEW_REQUIRE_STAGE2': 'true'})
    assert result.exit_code == 1
    assert 'Missing Stage 2 recommendation sections' in (result.stdout + result.stderr)


def test_r12_stage2_requires_minimum_structure_when_enabled(global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + 'Stage 2 推荐门禁上下文摘要\n'
        + '- task_goal: 调整 compliance-reviewer\n'
        + 'Stage 2 推荐门禁清单\n'
        + '- change_type: skill\n'
        + '验证：test passed\n'
        + '状态：完成（已验证：pytest -q test passed）\n'
    )
    result = run_hook(body, global_hook_path, env={'COMPLIANCE_REVIEW_REQUIRE_STAGE2': 'true'})
    assert result.exit_code == 1
    assert 'Incomplete Stage 2 recommendation structure' in (result.stdout + result.stderr)


def test_r13_stage2_structured_block_passes_when_enabled(global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + stage2_recommendation_block()
        + stage2_executable_recheck_block()
        + '验证：test passed\n'
        + '状态：完成（已验证：pytest -q test passed）\n'
    )
    result = run_hook(body, global_hook_path, env={'COMPLIANCE_REVIEW_REQUIRE_STAGE2': 'true'})
    assert result.exit_code == 0


def test_r14_stage2_suggest_blocking_requires_executable_rechecks(global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + stage2_recommendation_block()
        + '验证：test passed\n'
        + '状态：完成（已验证：pytest -q test passed）\n'
    )
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1
    assert 'Missing executable Stage 2 recheck commands' in (result.stdout + result.stderr)


def test_r15_stage2_executable_rechecks_pass_when_commands_match(global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + stage2_recommendation_block()
        + stage2_executable_recheck_block()
        + '验证：test passed\n'
        + '状态：完成（已验证：pytest -q test passed）\n'
    )
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 0


def test_r16_stage2_executable_rechecks_fail_on_output_mismatch(global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + stage2_recommendation_block()
        + stage2_executable_recheck_block(expect_stdout='not-json-ok')
        + '验证：test passed\n'
        + '状态：完成（已验证：pytest -q test passed）\n'
    )
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1
    assert 'Executable Stage 2 recheck failed' in (result.stdout + result.stderr)


def test_r17_environment_sensitive_claim_requires_real_environment_evidence(global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + '本次修改依赖真实 session 数据、真实路径挂载和 fzf 交互行为。\n'
        + '验证：node --test tests/codex-sess.test.js 全部通过\n'
        + '状态：修改（已验证：node --test tests/codex-sess.test.js exit 0）\n'
    )
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 1
    assert 'real-environment verification evidence' in (result.stdout + result.stderr)


def test_r18_environment_sensitive_claim_passes_with_explicit_real_environment_evidence(global_hook_path) -> None:
    body = (
        compliance_receipt_block()
        + '本次修改依赖真实 session 数据、真实路径挂载和 fzf 交互行为。\n'
        + '运行结果：使用真实 ~/.codex/sessions 数据执行展示检查，确认出现 js/poc-design2 分组。\n'
        + '状态：修改（已验证：node display-check.js exit 0；real session data verified）\n'
    )
    result = run_hook(body, global_hook_path)
    assert result.exit_code == 0
