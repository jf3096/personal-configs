---
name: self-improve-skill
description: 当用户希望把一个任务做成“需求澄清 -> expectation 对齐 -> acceptance 对齐 -> 自动迭代优化”的闭环时使用。默认采用提问式流程：每轮只问一个关键问题，优先提供可选项并标注推荐项。流程必须先询问需求并进入 clarify，待 PRD 收敛后再由 AI 总结 {summary_a_name}，随后固化 expectations 与 acceptance，最后按用户确认的轮数与目标分数执行自动 loop 并记录每轮结果。
---

# Self Improve Skill

用于把模糊需求收敛为可执行闭环，并持续迭代到可验收状态。

## 触发条件

1. 用户要求“自动进化/自动迭代优化”。
2. 用户要求先明确需求、expectation、acceptance，再执行。
3. 用户要求把过程与证据持久化记录在项目目录。

## 交互协议（默认提问式）

1. 默认每轮只问 1 个关键问题，不一次性抛出完整问卷。
2. 每个问题优先提供 2-4 个可选项，并标注推荐项（例如“B 推荐”）。
3. 必须保留“自定义答案”入口，避免把用户限制在固定选项里。
4. 只有在当前问题确认后，才能进入下一个问题并更新文档。
5. 若用户明确要求“直接给完整问卷”，才切换为批量提问模式。
6. 第一题必须是“需求本身”，不能先问 `{summary_a_name}` 命名。

## 目录契约（必须遵守）

所有产物都放在：`.self-improve-skill/{summary_a_name}/`

最小文件集合：

1. `prd.md`：需求与边界
2. `expectations.md`：期望结果与约束
3. `acceptance.md`：验收标准与量化门槛
4. `loop-config.json`：迭代参数
5. `runs/run-*/`：每轮执行证据
6. `runs/run-*/run-summary.json`：最终汇总

`{summary_a_name}` 生成规则：

1. 从用户目标提炼 3-6 个词。
2. 使用 kebab-case，仅小写字母、数字、连字符。
3. 如果用户指定名称，优先使用用户指定。
4. 若用户未指定，必须在 PRD clarify 完成后由 AI 基于 PRD 总结名称并让用户确认。

## 强制流程（按顺序）

### 1) 需求采集并写入 PRD

1. 先用提问式收集需求，不要直接假设。
2. 第一题必须询问“你要解决什么需求/问题”，禁止先问命名类问题。
3. 问题尽量用选项形式给用户快速选择，并允许自定义。
4. 将已确认信息写入 `prd.md`。
5. 若存在不确定项，显式写入 `Open Questions`。

### 2) Clarify PRD（可多轮）

1. 采用渐进澄清：目标 -> 范围 -> 非目标 -> 输入输出 -> 约束 -> 风险。
2. 每轮最多推进一个未确认点，避免用户认知负担过大。
3. 任何模糊描述都要追问，直到可执行。
4. 每轮澄清后更新 `prd.md`，保留版本注记。

### 3) PRD 收敛后生成 `{summary_a_name}`

1. 仅当 PRD 的目标、范围、边界已经清晰后，才可进入命名阶段。
2. 由 AI 基于 PRD 提供 2-4 个候选名称（kebab-case）并标注推荐项。
3. 用户确认后再创建/迁移 `.self-improve-skill/{summary_a_name}/` 目录。
4. 将命名决策和理由写入 `prd.md` 的 `Naming Decision` 小节。

### 4) 设计并确认 Expectations

1. 基于 PRD 提出 expectation 草案。
2. 以“选项 + 推荐”的方式让用户确认每一组 expectations。
3. 用户修改后继续 clarify，直到每条 expectation 都可验证、无二义。
4. 最终写入 `expectations.md`。

### 5) 设计并确认 Acceptance

1. 将 expectations 映射为验收标准（质量、时延、成本、稳定性）。
2. 使用选择式问题确认通过阈值与失败条件。
3. 用户确认后固化到 `acceptance.md`。

### 6) Loop 执行前输出“预演”（必须）

1. 在执行自动迭代 loop 之前，必须先输出 `预演` 小节。
2. `预演` 必须覆盖即将执行的每一个关键步骤，至少包含：
   - 参数确认（max loops / target score / execute-cmd / score-cmd / quality-cmd）
   - 执行主命令（`self-improve-loop.sh`）
   - 单轮评分与质量检查
   - 证据写入（`iteration.json` / `feedback.md` / `run-summary.json`）
   - 停止条件判断（达标停止或继续下一轮）
3. `预演` 的每个步骤都必须明确：
   - 输入（Input）
   - 执行动作（Action）
   - 期望输出（Expected Output）
4. 若任何关键步骤缺少输入或期望输出定义，禁止进入 loop 执行，必须先回到上游阶段澄清。
5. `预演` 输出后，必须向用户发起确认（例如：`是否按此预演执行？`）。
6. 仅当用户给出明确同意（如“确认执行 / 按此执行 / yes”）后，才允许进入 loop 执行；若用户要求调整，必须先更新预演再二次确认。
7. 推荐输出模板：

```md
## 预演

步骤 1：参数确认
- 输入：用户确认的 max loops、target score、执行命令
- 执行动作：生成并校验 `loop-config.json`
- 期望输出：参数完整且可执行，进入命令执行阶段

确认问题：是否按此预演执行？
```

### 7) 启动自动迭代 Loop

1. 在执行前必须询问并确认：
   - 最大轮数（max loops）
   - 目标分数（target score）
2. 只有当“预演确认”已通过时，才可启动本阶段；未确认一律禁止执行。
3. 上述两个参数优先用选项式提问，给默认推荐值与风险说明。
4. 将确认结果写入 `loop-config.json`。
5. 使用项目脚本执行：

```bash
bash scripts/rule-verifier/self-improve-loop.sh \
  --workspace ".self-improve-skill/{summary_a_name}" \
  --max-loops <n> \
  --target-score <score> \
  --execute-cmd '<cmd>' \
  --score-cmd '<cmd>' \
  --quality-cmd '<cmd-optional>'
```

6. 每轮都要写入 `runs/run-*/iter-*/iteration.json` 与 `feedback.md`。
7. 达标即停止；未达标则 `loop back` 并继续下一轮。

## 与 skill-creator / ralph-loop 的关系

1. 借鉴 `skill-creator`：先澄清、后评估、再迭代，不做一次性拍脑袋交付。
2. 借鉴 `run_loop.py`：多轮评分、最佳结果选择、历史保留。
3. 借鉴 `ralph-loop`：每轮都保留 gate 证据与 loop-history。

## 输出要求

每次对用户汇报都应包含：

1. 当前阶段（PRD / Expectations / Acceptance / 预演 / Loop）
2. 本轮新增或变更的文件路径
3. 本轮关键决策（为什么这样收敛）
4. 下一步需要用户确认的最小问题集合（默认 1 题，附选项与推荐）
5. 若当前阶段为 `预演`，必须逐条给出“关键步骤 -> 输入 -> 期望输出”清单。
6. 若当前阶段为 `预演`，必须显式给出“是否按此预演执行”的确认问题；未获确认前不得进入 `Loop`。

## 失败闭环要求

当自动迭代失败时，必须输出：

1. 未通过的门槛项
2. 失败证据路径
3. 下一轮修正策略
4. 是否继续下一轮（由用户确认）
