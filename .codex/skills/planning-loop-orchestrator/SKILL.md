---
name: planning-loop-orchestrator
description: 当用户说“策划”、要求先规划后执行，或需要多方案选择时使用。该技能强制输出四段闭环（1.需求 2.执行大致路径 3.结果 4.验收质量考核），提供 A/B/C 方案选择，并通过 progress.txt 记录每轮反思；验收失败必须 loop back 到第 1 点。
---

# Planning Loop Orchestrator

用于“先策划再执行”的标准化闭环，适合需求不稳定、风险较高或需要先对齐方案的任务。

## 触发条件

1. 用户明确说“策划”。
2. 用户要求“先规划再实现”。
3. 需要提供多个执行方式并由用户选择。

## 必须流程（按顺序）

1. 生成候选方案（A/B/C）并标注推荐项（默认 B）。
2. 按固定结构输出四段内容：
   - 1) 需求
   - 2) 执行大致路径
   - 3) 结果
   - 4) 验收质量考核
3. 用户选择后再执行；未选择时只输出候选方案。
4. 每轮把四段内容追加到 `progress.txt`，并写 Reflection + Decision。
5. 验收失败时必须在 Decision 写明：`loop back 到 1) 需求`。

## 执行入口（项目内）

先出方案（不执行）：

```bash
bash scripts/rule-verifier/planning-loop.sh \
  --goal "<goal>" \
  --context "<context>"
```

选方案后执行：

```bash
bash scripts/rule-verifier/planning-loop.sh \
  --goal "<goal>" \
  --choice B \
  --execute-cmd '<execute_cmd>' \
  --quality-cmd '<quality_gate_cmd>'
```

## 产物与证据

每次 run 至少检查：

1. `plan/plan-options.md`（A/B/C）
2. `plan/selected-plan.md`（四段规划）
3. `plan/progress.txt`（每轮反思与决策）
4. `loop-history.tsv`（通过/失败趋势）
5. `run-summary.json`（最终汇总）

默认持久化路径：`.artifacts/planning-loop/run-*`

## 失败闭环要求

当技能或脚本变更后，至少提供：

1. 正例 x1（应通过）
2. 负例 x1（应回环失败）
3. 待选择样例 x1（仅生成方案）

并在交付中给出命令、退出码、关键产物路径。
