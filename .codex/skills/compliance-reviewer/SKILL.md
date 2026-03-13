---
name: compliance-reviewer
description: 在输出“完成/修改”结论前执行最终合规门禁。用于检查事实证据、双层 verdict、风险披露与失败闭环，适用于代码与配置变更交付场景。
---

# Compliance Reviewer

用于“完成/修改”结论的最终门禁，防止无证据交付和推导型假证据。

## 双阶段模型

`compliance-reviewer` 采用双阶段模型：

1. **Stage 1：标准门禁（阻断层）**
检查状态行、证据真实性、双层 verdict、compliance 回执、失败闭环。
2. **Stage 2：推荐门禁（建议层）**
基于上下文给出结构化推荐清单；高强度推荐项必须提供可执行复验命令并由 hook 重跑。

## Agent-First 交付契约

当输出完成/修改结论时，正文必须同时包含：

1. `Compliance Verdict: PASS|FAIL`
2. `Delivery Verdict: PASS|PASS_WITH_HIGH_RISK|BLOCKED`
3. `Release Advice: Ship|Hold`

说明：

- `Compliance Verdict` 代表汇报与证据契约是否合规。
- `Delivery Verdict` 代表交付目标是否真实达成。
- 高风险路径下禁止 `Delivery Verdict: PASS`。

## 高风险与强制复测

命中以下任一条件即视为高风险：

1. 新增依赖、DB migration、公共 API/协议变更、生产权限/配置脚本变更。
2. 变更规模超过阈值：`files_changed > 5` 或 `line_delta > 200`。

高风险路径规则：

1. 必须包含 `TDD-Strict Revalidation` 段落。
2. 必须提供 `TDD Revalidation Command: <cli command>`。
3. 该命令输出必须为 JSON（CLI JSON 契约），字段至少包含：
   - `revalidation_status`
   - `test_evidence`
   - `run_evidence`
4. `Delivery Verdict: PASS_WITH_HIGH_RISK` 必须对应复测状态 `pass`。
5. TDD CLI 调用失败（命令不存在/超时/非 JSON/字段非法）时，只允许 `Delivery Verdict: BLOCKED`。
6. 可复用适配器模板：`references/tdd-cli-adapter-template.md`。

## 必须项（简版）

1. 最后一行必须为标准状态行之一：
- `状态：完成（已验证：<command/results>）`
- `状态：修改（已验证：<command/results>）`
- `状态：修改（未验证：<reason>）`
2. 禁止用推测性表述替代证据（例如 `should work`、`probably`、`理论上`、`应该可以`）。
3. 若存在可执行主张（可启动/可部署/可调用），必须提供运行证据（`command + result + exit code`）。
4. 若曾验证失败，必须给出“失败 -> 修复 -> 复验”的闭环证据。
5. 汇报正文必须包含 compliance 回执块：
- `Compliance Skill: $compliance-reviewer`
- `Hook Command: ...pre-completion-check.sh`
- `Hook Exit: <code>`
- `Hook Verdict: PASS|FAIL`
6. Stage 2 推荐清单默认应包含；当 `COMPLIANCE_REVIEW_REQUIRE_STAGE2=true` 时会被 hook 强制检查。

## 输出结构建议（动态任务树）

推荐使用动态任务树而非固定编号，例如：

- `W1`, `W1.1`, `W2.3`

编号不是门禁项，语义完整性才是门禁项。

## Stage 2 输入摘要

- `task_goal`
- `change_objects`
- `change_summary`
- `executed_commands`
- `existing_evidence`
- `risk_points`

## Stage 2 输出契约

- `change_type`
- `change_summary`
- `impact_scope`
- `recommended_checks`
- `reason`
- `severity`
- `requires_user_confirmation`

## 执行入口

Hook 检查：

```bash
cat /tmp/response-draft.txt | bash hooks/pre-completion-check.sh
```

显示 Hook 判定字段：

```bash
cat /tmp/response-draft.txt | COMPLIANCE_REVIEW_VERBOSE=true bash hooks/pre-completion-check.sh
```

回归测试：

```bash
/home/jf3096/.codex/skills/compliance-reviewer/run-compliance-tests.sh
```

核心回归：

```bash
/home/jf3096/.codex/skills/compliance-reviewer/run-compliance-tests.sh --core-only
```
