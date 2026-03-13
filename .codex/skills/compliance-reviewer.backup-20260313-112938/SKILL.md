---
name: compliance-reviewer
description: 在输出“完成/修改”结论前执行最终合规门禁。用于检查标准状态行、验证证据、风险披露与失败闭环，适用于代码与配置变更交付场景。
---

# Compliance Reviewer

用于“完成/修改”结论的最终门禁，防止无证据交付和不完整汇报。

## 双阶段模型

`compliance-reviewer` 采用双阶段模型：

1. **Stage 1：标准门禁**
检查标准状态行、验证证据、compliance 回执、失败闭环。
2. **Stage 2：推荐门禁**
在 Stage 1 完成后，基于本轮真实变更上下文生成结构化推荐门禁清单；对于高强度推荐项，必须补充可执行复验命令，并由 hook 实际重跑。

## 何时触发

1. 即将给出完成/修改结论。
2. 已修改代码或配置并准备交付。
3. 规则、hook、门禁策略发生变化。
4. 无法验证，需要给出未验证说明。

## 必须项（简版）

1. 最后一行必须为标准状态行之一：
- `状态：完成（已验证：<command/results>）`
- `状态：修改（已验证：<command/results>）`
- `状态：修改（未验证：<reason>）`
2. 至少提供一类可观测证据：测试命令、运行命令、日志输出。
3. 禁止用推测性表述替代证据。
4. 若曾验证失败，汇报必须按“先失败 -> 后修复 -> 再通过”给出闭环证据。
5. 规则变更必须提供：正例 x1、负例 x1、对抗样例 x1。
6. 汇报正文必须包含 compliance 回执块：
- `Compliance Skill: $compliance-reviewer`
- `Hook Command: ...pre-completion-check.sh`
- `Hook Exit: <code>`
- `Hook Verdict: PASS|FAIL`
7. 若改动依赖真实路径、真实数据、挂载方式、交互工具或本机环境，必须额外说明“真实环境验证”状态；fixture/样例/单元测试通过不能替代真实环境验证。
8. 完成/修改回复默认应包含 Stage 2 结构化推荐门禁清单；若当前通过 hook 强制执行，则由 `COMPLIANCE_REVIEW_REQUIRE_STAGE2=true` 控制。

## Stage 2 输入摘要

生成推荐门禁前，主代理应先整理最小上下文：

- `task_goal`
- `change_objects`
- `change_summary`
- `executed_commands`
- `existing_evidence`
- `risk_points`

这些字段用于回答：
本轮任务要达成什么、改了什么、怎么改的、已经验证到什么程度、还存在哪些验证缺口。

## Stage 2 输出契约

推荐门禁清单至少应包含以下字段：

- `change_type`
- `change_summary`
- `impact_scope`
- `recommended_checks`
- `reason`
- `severity`
- `requires_user_confirmation`

其中：

- `change_type`：本轮主要变更类型
- `impact_scope`：影响范围
- `recommended_checks`：推荐执行的检查项
- `severity`：推荐强度，例如 `suggested` / `strongly_suggested` / `suggest_blocking`
- `requires_user_confirmation`：是否必须由用户确认后才执行

Stage 2 的目标是给出“更贴近当前变更”的验证建议，而不是替代 Stage 1 的统一门禁。

## Stage 2 可执行复验

当 Stage 2 推荐清单中的 `severity` 为 `strongly_suggested` 或 `suggest_blocking` 时，报告中必须提供：

- `Stage 2 可执行复验命令`
- 至少一条 `- run: <command>`
- 与之匹配的 `expect_exit`，必要时补 `expect_stdout` / `expect_stderr`

hook 会重新执行这些命令。仅在正文里声称“已经 curl/pytest/docker 验证过”但不提供可执行复验命令，不再视为充分闭环。

## 真实环境验证规则

当改动结果受以下因素影响时，必须区分“样例验证”和“真实环境验证”：

- 真实路径或挂载路径
- 本机 session / 数据目录
- 交互工具行为，例如 `fzf`
- 外部环境差异导致的表现变化

可接受的已验证结论应至少满足其一：

- 明确给出真实环境复验命令、退出码和关键输出
- 正文明确写出使用真实数据或真实环境完成了复验

若只能证明 fixture、sample、mock、unit test 通过，则最终状态必须写成未验证，或补做真实环境复验。

详细规则见：`references/rules.md`
证据清单见：`references/evidence.md`
汇报模板见：`references/report-template.md`

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
