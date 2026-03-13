# Report Template

## [证据契约] 总结
- 本 turn 目标：
- 本 turn 结果：

## 任务树（动态）
- `W1`：
- `W1.1`：
- `W2`：

## DoD（Definition of Done）
- 必备证据类型：`command / result / exit code`
- 证据数量下限：
- 失败时是否给出失败证据：

## Stage 2 推荐门禁上下文摘要
- task_goal:
- change_objects:
- change_summary:
- executed_commands:
- existing_evidence:
- risk_points:

## Stage 2 推荐门禁清单
- change_type:
- change_summary:
- impact_scope:
- recommended_checks:
- reason:
- severity:
- requires_user_confirmation:

## Stage 2 可执行复验命令
- run:
- expect_exit:
- expect_stdout:
- expect_stderr:

## 高风险评估
- high_risk:
- risk_trigger:
- files_changed:
- line_delta:
- Auto Remediation Attempts:

## TDD-Strict Revalidation（高风险必填）
TDD Revalidation Command:

## 初次验证失败
- command:
- result:

## 修复动作
- 修改文件：
- 修改点：

## 复验结果
- command:
- result:

## Verdict（必填）
Compliance Verdict: PASS|FAIL
Delivery Verdict: PASS|PASS_WITH_HIGH_RISK|BLOCKED
Release Advice: Ship|Hold

## Compliance 回执（必填）
Compliance Skill: $compliance-reviewer
Hook Command: cat /tmp/response-draft.txt | COMPLIANCE_REVIEW_VERBOSE=true bash .../pre-completion-check.sh
Hook Exit: 0|1
Hook Verdict: PASS|FAIL

## 最终状态行
状态：完成（已验证：...）
或
状态：修改（已验证：...）
或
状态：修改（未验证：...）
