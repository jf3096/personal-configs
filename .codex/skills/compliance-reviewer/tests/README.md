# Compliance Reviewer Test Suite

本目录提供 `pre-completion-check.sh` 的规格驱动一致性验证。

## 运行方式

```bash
python3 -m pytest -q /home/jf3096/.codex/skills/compliance-reviewer/tests
```

## 规则到测试映射

- `R1` 标准状态行必填
  - `test_hook_rules.py::test_r1_requires_standard_status_when_claiming_completion`
  - `test_hook_examples.py::test_example_matrix[B_claim_done_no_status-...]`
- `R2` 已验证分支需证据
  - `test_hook_rules.py::test_r2_requires_evidence_in_verified_branch`
- `R3` 推测词阻断
  - `test_hook_rules.py::test_r3_blocks_speculative_language`
  - `test_hook_properties.py::test_p3_speculative_words_fail_verified_branch`
- `R4` 未验证分支允许通过
  - `test_hook_rules.py::test_r4_allows_unverified_with_reason`
  - `test_hook_properties.py::test_p2_unverified_branch_passes_without_positive_evidence`
- `R5` 最后一行语义
  - `test_hook_rules.py::test_r5_only_last_non_empty_line_is_status`
  - `test_hook_properties.py::test_p4_last_non_empty_line_controls_status_evaluation`
- `R6` bypass 语义
  - `test_hook_rules.py::test_r6_bypass_short_circuits_all_checks`
- `R7` verbose 可观测
  - `test_hook_rules.py::test_r7_verbose_prints_decision_fields`
  - `test_hook_examples.py::test_verbose_probe`
- `R8` 全局与技能 hook 一致性
  - `test_hook_consistency.py::test_global_and_skill_hook_behavior_is_identical`
  - `test_hook_consistency.py::test_global_and_skill_hook_file_hash_identical`
- `R11` Stage 2 可开关强制策略
  - `test_hook_rules.py::test_r10_stage2_not_required_when_toggle_disabled`
  - `test_hook_rules.py::test_r11_stage2_required_when_toggle_enabled`
  - `test_hook_rules.py::test_r12_stage2_requires_minimum_structure_when_enabled`
  - `test_hook_rules.py::test_r13_stage2_structured_block_passes_when_enabled`
- `R12` 高强度 Stage 2 必须有可执行复验并由 hook 重跑
  - `test_hook_rules.py::test_r14_stage2_suggest_blocking_requires_executable_rechecks`
  - `test_hook_rules.py::test_r15_stage2_executable_rechecks_pass_when_commands_match`
  - `test_hook_rules.py::test_r16_stage2_executable_rechecks_fail_on_output_mismatch`
- `R0/R5-R8` 双 verdict + 高风险强制 TDD CLI JSON
  - `test_delivery_gate.py::*`
  - `test_hook_rules.py::test_r19_requires_dual_verdict_fields`
  - `test_hook_rules.py::test_r20_high_risk_cannot_use_plain_pass`
  - `test_hook_rules.py::test_r21_high_risk_requires_tdd_command`
  - `test_hook_rules.py::test_r22_high_risk_pass_with_tdd_json`
  - `test_hook_rules.py::test_r23_high_risk_tdd_failure_is_allowed_only_for_blocked`

## 对抗与已知局限

`test_hook_adversarial.py` 包含对抗样例，其中 `xfail` 用例表示当前实现已知局限：

- 代码块内关键字可能被误判为证据。
- URL 字符串中的关键词可能触发声明判定。

这些 `xfail` 用例用于防止“已知问题被忽略”，并记录改进方向。
