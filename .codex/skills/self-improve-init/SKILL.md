---
name: self-improve:init
description: Initialize a baseline for a later self-improve loop by interviewing the user and writing baseline docs into a user-specified workspace. Use this whenever the user wants to turn a business idea into a first baseline for later iteration around execution results.
disable-model-invocation: true
---

# Self Improve Init

## Overview

Initialize a baseline for later self-improve iterations.

This skill organizes the user's idea into three workspace files:

- `<workspace>/prd.md`
- `<workspace>/execution-playbook.md`
- `<workspace>/benchmark.md`

This is a task skill. When the user invokes it directly, stay inside the init workflow until the draft baseline is written or the smallest missing field is identified.

This baseline uses a three-layer model:

- `prd.md`：稳定任务定义层
- `execution-playbook.md`：执行层与默认主迭代层
- `benchmark.md`：评测层

This skill supports two entry modes:

1. `自述 baseline`：当用户已经大致知道 baseline 应该如何定义时使用。以用户描述为主；如果边界有些模糊，可以用 `brainstorming` 做轻量矫正。
2. `含糊 baseline 创作模式`：当用户只知道想要什么结果，但并不知道 baseline 该怎么设计时使用。以 agent 起草为主；必须先用 `brainstorming` 收敛目标与候选路径，再在需要时结合外部事实核实（例如 web research、在线验证、官方页面核实）补足当前网站、数据源、页面结构或外部约束，最后基于两者生成一个可执行、可迭代、适合后续 loop 稳定化的推荐 baseline 草案。

## Hard Gates

- 不负责自动 loop
- 不默认运行执行对象
- 不自动优化执行策略
- 不为不同执行对象设计分支流程
- 不在 init 阶段切去执行业务任务本身，除非用户在后续选择了可选的真实 run 复核
- 真实 run 复核最多执行一次，且只能在用户明确选择后进行
- 即使在 `含糊 baseline 创作模式` 中，agent 也只能帮助用户起草 baseline，不得未经确认就把起草方案当成最终事实
- `含糊 baseline 创作模式` 中，agent 起草完推荐 baseline 草案后，必须先让用户确认或修改；确认前不得把草案写成最终 baseline

## Question Flow

1. 首轮先给两个模式选项：`自述 baseline` / `含糊 baseline 创作模式`
2. 若用户选择 `自述 baseline`，先收集用户自己的 baseline 描述与业务目标
3. 若用户选择 `含糊 baseline 创作模式`，先收集用户想要的结果，再由 agent 起草一版推荐 baseline 草案
4. 让用户确认、修改或重起该推荐 baseline 草案
5. 再问 workspace 路径
6. 立即创建 draft baseline
7. 再问执行手册定义
8. 再问真实 benchmark case
9. 补齐期望输出、评分维度、通过标准
10. baseline 可用后，询问是否做一次可选的真实 run 复核
11. 若用户未准备好，则跳过真实 run 并完成 baseline

## Rules

- 一次只问一个关键问题
- 不改变用户原意
- 优先收集最小必要信息
- 缺失项标记为“待确认”
- 用户必须提供至少一个真实 benchmark case
- 每轮都必须显式汇报：当前阶段、已确认项、缺失项、是否已落盘、下一步问题
- `prd.md` 的 `业务目标` 只允许描述“用户真正想完成的业务任务”，不得写 baseline 的系统用途、loop 目标、初始化目的或文档自身用途
- `baseline`、`self-improve`、`loop`、`初始基线`、`可迭代` 这类词，如果用于说明这套文档未来怎么被使用，应放在 agent 心智、实现策略或其他 section 中，不得覆盖 `prd.md` 的 `业务目标`
- 写 `业务目标` 时，先回答“用户到底要做成什么”，再考虑“这份 baseline 后续怎么被用”
- `prd.md` 是稳定任务定义层，默认只写业务目标、高层执行骨架、预期结果、边界与约束
- `execution-playbook.md` 是执行层与默认主迭代层，但它应是“当前执行真相”文档，不是历史观察堆栈；默认承载执行目标与职责、输入、输出、当前执行方案、候选降级路径与待验证项、后续优化方向
- `benchmark.md` 是评测层，默认承载真实 benchmark case、期望输出、评分维度与通过标准
- `prd.md` 的 `执行路径` 只允许写高层骨架，不得写 selector、wait 条件、fallback、retry、字段修正规则等低层执行细节；这些内容默认写入 `execution-playbook.md`
- `execution-playbook.md` 的 `输入` 只允许写当前已确认、可执行、可配置的输入项；未验证完成的备选入口、候选方案或不确定参数，不得写成输入主配置，应写入 `候选降级路径与待验证项`
- 一旦执行过真实 run 复核，`execution-playbook.md` 的 `输入`、`输出`、`当前执行方案` 中不得继续保留 `待确认` 或 `xxx：待确认` 这类半确认条目；无法确认的内容必须移动到 `候选降级路径与待验证项` 或 `后续优化方向`
- 真实 run 之后，`execution-playbook.md` 必须采用“正文收敛式回写”，把已验证观察折叠进正文；不得在 playbook 中长期保留 `来自真实 run 观察`、`真实 run 复核记录` 这类历史附加层
- 当用户直接调用本 skill 时，第一条实质性问题必须先提供两个模式选项，而不是直接逼用户定义 baseline
- `自述 baseline` 模式中，以用户为主；若边界不清，可使用 `brainstorming` 做轻量矫正，但不能替代用户的核心意图
- `含糊 baseline 创作模式` 中，以 agent 起草为主；用户只需说明想要的结果，agent 负责在可行路径中起草一个推荐 baseline
- `含糊 baseline 创作模式` 中，agent 不得直接凭印象起草 baseline；必须先完成一次最小 `brainstorming` 收敛，再在需要时结合外部事实核实，然后才能形成推荐 baseline 草案
- `含糊 baseline 创作模式` 中，如果主题依赖当前网页、外部数据源、站点结构、时效性信息或真实约束，必须使用 web research、在线验证或其他可留痕的外部事实核实方式，先补足关键事实，再起草 baseline
- 在本 skill 内使用 `brainstorming` 时，应吸收其“理解目标、比较候选路径、给出推荐”的核心作用；已确认的推荐 baseline 草案就是本流程的设计产物，不额外创建 `docs/plans/*` 设计文档，也不切换到 `writing-plans`
- `含糊 baseline 创作模式` 中，agent 起草后必须显式说明：这是 `推荐 baseline 草案`，用户有权直接确认、局部修改、或整体推翻后重起
- `含糊 baseline 创作模式` 中，只有在用户明确确认该草案后，才可将其视为已确认 baseline，并继续写入 `prd.md` / `execution-playbook.md` / `benchmark.md`
- `含糊 baseline 创作模式` 中，在草案确认完成前，agent 不得转去追问 `workspace`、benchmark、评分维度或其他后续缺失项；当前轮的唯一关键问题必须是：确认、修改，或重起该草案
- 无论哪种模式，agent 都应优先选择一套后续更容易验证、重复执行、并能被 loop 稳定化的 baseline 结构与执行策略
- 当 agent 起草 baseline 时，必须显式区分：哪些内容属于 `prd.md` 的高层执行骨架，哪些内容属于 `execution-playbook.md` 的当前执行方案，哪些内容只属于 `候选降级路径与待验证项`
- 若已执行 `brainstorming` 或外部事实核实，必须在回报中分别显式标记，不得用含糊的 `research：已使用` 混称所有动作
- 只要已确认 `workspace` 和最小业务目标，并且在 `含糊 baseline 创作模式` 下草案已获用户确认，就必须立即创建 draft 文件，未知字段统一写为“待确认”
- 每次写入或更新后，都要运行 `python3 .codex/skills/self-improve-init/scripts/validate_baseline.py --workspace "<workspace>"` 来决定下一步最小缺失项
- `真实 run 复核` 是可选步骤，不是阻断 baseline 的必经步骤
- 只有当用户明确同意且条件已具备时，才允许执行一次真实 run 复核
- 如果用户未准备好、缺执行条件、或不希望执行真实 run，必须跳过该步骤，并继续完成 baseline 文档
- 真实 run 复核仅用于补强 `prd.md`、`execution-playbook.md`、`benchmark.md` 与证据文件，不进入自动 loop
- 真实 run 复核默认优先回写 `execution-playbook.md`；只有发现评测盲区时才回写 `benchmark.md`；只有确认高层方法论发生变化时才回写 `prd.md`

### `prd.md` 语义边界

`prd.md` 的 `业务目标` 是任务目标，不是文档用途说明。

错误示例：

- `建立一个可重复执行的 baseline，作为后续 self-improve loop 的初始基线`

正确示例：

- `通过 Playwright MCP 获取微博移动端实时热点主榜前 10 条热搜，并输出为结构化结果`

如果 agent 想表达“这套内容后续可被 loop 使用”，那是 agent 的内部建模或其他 section 的上下文，不得替代 `业务目标` 本身。

### `执行路径` 语义边界

`prd.md` 的 `执行路径` 只写高层骨架，不写低层执行细节。

正确示例：

- `打开目标页面，等待榜单区域出现，提取条目并输出结构化结果`

错误示例：

- `使用 page.locator(\"...\") 等待 5 秒，若失败则切换 fallback selector 并 retry 3 次`

如果 agent 需要表达当前执行方案、候选降级路径、等待条件、字段修正规则，应写入 `execution-playbook.md`，而不是写入 `prd.md` 的 `执行路径`。

### `execution-playbook.md` 语义边界

`execution-playbook.md` 是执行层与默认主迭代层。

这里应该承载：

- 执行目标与职责
- 输入与输出约束
- 当前执行方案
- 候选降级路径与待验证项
- 后续优化方向

如果 agent 还不能确定最终方法，也可以先把候选执行策略写在这里，但应放在 `候选降级路径与待验证项`，而不是污染 `输入` 或 `当前执行方案`。

额外边界：

- `输入` 只放当前已确认、可执行、可配置的内容
- 若某个备选入口、候选方案或参数仍未验证完成，不得写成 `输入` 的主配置项
- 这类不确定信息必须写入 `候选降级路径与待验证项`
- 一旦完成真实 run，`输入`、`输出`、`当前执行方案` 应被回写成可执行状态，不得继续残留占位项
- `execution-playbook.md` 只保留当前成立的执行方案；历史失败闭环、试验过程、run 观察留在 `evidence/`

## Workflow

### 1. 进入 init 模式

当用户直接调用本 skill 时：

1. 只执行 baseline 初始化工作，不切换去执行业务任务本身。
2. 第一条回复必须包含：
   - 当前阶段
   - 已确认项
   - 缺失项
   - 是否已落盘
   - 两个模式选项
   - 下一个唯一关键问题

### 2. 选择 baseline 入口模式

首轮必须提供两个选项：

1. `自述 baseline`
   - 适用于：用户已经大致知道 baseline 要做什么、怎么做
   - 行为：以用户描述为主，必要时用 `brainstorming` 澄清边界
2. `含糊 baseline 创作模式`
   - 适用于：用户只知道想要什么结果，不知道 baseline 该怎么设计
   - 行为：agent 先用 `brainstorming` 收敛目标与候选路径；若依赖外部事实，再结合 web research / 在线验证查关键事实；然后起草一个推荐 baseline

如果用户不主动选，agent 可以根据描述清晰度推荐一个模式，但仍要让用户确认。

### 3. 先收集最小可写入信息

最小可写入条件：

1. `业务目标` 已有最小可用描述
2. `workspace` 已确认，或用户接受默认值

额外要求：

- 在 `自述 baseline` 模式下，业务目标与 baseline 轮廓主要来自用户自述
- 在 `含糊 baseline 创作模式` 下，业务目标可以先来自用户想要的结果；高层任务骨架与候选执行策略由 agent 起草，但必须先向用户说明这是 `推荐 baseline 草案`
- 在 `含糊 baseline 创作模式` 下，除了 `业务目标` 与 `workspace`，还必须有 `用户对推荐 baseline 草案的确认`，才算满足最小可写入条件

在达到最小可写入条件之前，只能继续追问最小缺失项。

### 4. 起草推荐 baseline（仅 `含糊 baseline 创作模式`）

如果用户选择 `含糊 baseline 创作模式`，则在写文件前必须先完成：

1. 用 `brainstorming` 把“想要的结果”收敛成：
   - 建议的输入
   - 建议的输出
   - 一条高层推荐执行骨架
   - 2-3 条候选执行路径与推荐方案
   - 初步边界与约束
2. 若主题依赖时效性或外部事实，使用 web research、在线验证或其他可留痕的外部事实核实方式补充：
   - 目标网站/平台的当前结构或入口
   - 关键页面或数据源
   - 可能的限制条件
3. 基于 `brainstorming` 的推荐路径与已核实的外部事实，向用户说明：这是 `推荐 baseline 草案`，不是已经最终确认的 baseline；并明确哪些内容将进入 `prd.md`，哪些内容将进入 `execution-playbook.md` 的“当前执行方案”，哪些内容只应进入“候选降级路径与待验证项”
4. 当前轮必须以草案确认问题收尾，不得在同一轮继续追问 `workspace` 或其他后续缺失项

### 5. 用户确认推荐 baseline 草案（仅 `含糊 baseline 创作模式`）

当 agent 完成推荐 baseline 草案后，必须先向用户发起确认。

用户必须拥有以下权利：

1. 直接确认该草案
2. 指定局部修改后再确认
3. 明确否决当前草案，并要求 agent 重起一版

在用户确认前，agent 必须：

1. 明确标记 `草案状态：待用户确认`
2. 不得把草案写成最终 baseline
3. 不得跳过确认步骤直接进入文件写入
4. 不得转去询问 `workspace`、benchmark、评分维度、通过标准等后续问题
5. 当前轮的唯一关键问题必须是：请用户确认、修改，或推翻重起该草案

在用户确认后，agent 必须：

1. 明确标记 `草案状态：已确认` 或 `已修改后确认`
2. 记录用户修改点
3. 再进入文件写入阶段

### 6. 立即创建 draft baseline

一旦达到最小可写入条件，必须立刻执行：

```bash
bash .codex/skills/self-improve-init/scripts/init_workspace.sh --workspace "<workspace>"
```

然后基于当前已确认信息更新：

- `<workspace>/prd.md`
- `<workspace>/execution-playbook.md`
- `<workspace>/benchmark.md`

未知字段统一写为“待确认”。

### 7. 写后必校验

每次创建或更新 baseline 后，必须执行：

```bash
python3 .codex/skills/self-improve-init/scripts/validate_baseline.py --workspace "<workspace>"
```

校验结果用于决定：

1. 是否已经达到 baseline usable
2. 下一轮只问哪个最小缺失项

### 8. baseline 可用后的可选真实 run 复核

当 baseline 已 usable 后，必须询问一次：是否要做真实 run 复核。

#### 8A. 用户选择不做，或暂时没准备好

如果用户：

- 明确说不要
- 还没准备好执行条件
- 缺账号、API key、权限、样本、环境或安全确认

则必须：

1. 明确标记“真实 run 复核：已跳过”
2. 记录跳过原因
3. 不把该步骤当作阻断项
4. 继续交付 baseline 文档

#### 8B. 用户明确选择做，且条件具备

只有同时满足以下条件，才允许执行一次真实 run：

1. 用户明确同意
2. `workspace` 已确认
3. baseline 已 usable
4. 已知最小高层执行骨架与最小候选执行策略
5. 不涉及高风险、破坏性或未获许可的操作

执行后必须：

1. 将真实 run 证据写入 `<workspace>/evidence/`
2. 默认基于真实观察优先回写 `execution-playbook.md` 的输入、输出、当前执行方案、候选降级路径与待验证项、后续优化方向
3. 回写方式必须是“正文收敛式回写”，即用真实观察改写 playbook 本体，而不是在每个章节下面追加 `来自真实 run 观察`
4. 若真实 run 已证明某个输入项、输出项或执行步骤可确认，则必须将对应条目改写为明确内容，不得继续保留 `待确认`
5. 若真实 run 仍不足以确认某个备选入口或候选方案，则必须把它写成 `候选降级路径与待验证项`，而不是继续放在 `输入` 或 `当前执行方案`
6. 历史失败闭环、试验过程、真实 run 观察细节必须写入 `evidence/`，不在 playbook 中堆叠保留
7. 若真实 run 暴露评测盲区，再回写 `benchmark.md` 的任务输入、评分维度、通过标准
8. 只有当真实 run 证明高层方法论发生变化时，才回写 `prd.md` 的执行路径、预期结果、边界与约束
9. 明确区分：哪些内容来自用户需求，哪些内容来自真实 run 观察

### 9. 对用户的回报格式

每轮都必须包含：

1. `当前阶段：模式选择 | 信息收集 | 推荐 baseline 起草 | 草案确认 | 已落草稿 | 补全草稿 | baseline 可用 | 真实 run 复核（可选）`
2. `已确认：...`
3. `待确认：...`
4. `已写入文件：...` 或 `尚未写入，原因：...`
5. 若当前处于 `含糊 baseline 创作模式`，必须额外说明：
   - `当前模式：含糊 baseline 创作模式`
   - `推荐 baseline 草案：...`
   - `草案状态：待用户确认 | 已确认 | 已修改后确认`
   - `brainstorming：已使用 | 未使用`
   - `外部事实核实：已使用 | 未使用 | 不需要`
   - 若 `草案状态` 仍为 `待用户确认`，则本轮唯一问题只能是草案确认相关问题
6. 若涉及真实 run，必须额外汇报：
   - `真实 run 复核：已执行 | 已跳过`
   - `原因：...`
7. 一个且仅一个关键问题

## Outputs

First ask the user to specify the baseline entry mode. In `含糊 baseline 创作模式`, ask for workspace only after the drafted baseline has been confirmed by the user.

If the user does not specify a workspace, default to `.self-improve/{{auto-created-name}}`, where `{{auto-created-name}}` is created by the AI agent.

If the chosen workspace does not exist, create it first.

Then write:

- `<workspace>/prd.md`
- `<workspace>/execution-playbook.md`
- `<workspace>/benchmark.md`

Use the local templates under `templates/` as the starting shape.

The templates are draft-first templates. They are allowed to contain `待确认` until the missing fields are collected.

If the user explicitly opts into one real run review and the conditions are ready, also write evidence under:

- `<workspace>/evidence/`

## Output Content

### `prd.md`
- 业务目标
- 执行路径
- 预期结果
- 边界与约束

### `execution-playbook.md`
- 执行目标与职责
- 输入
- 输出
- 当前执行方案
- 候选降级路径与待验证项
- 后续优化方向

### `benchmark.md`
- 任务背景
- 任务输入
- 期望输出
- 评分维度
- 通过标准

## Blocking Conditions

Do not finalize the draft yet if any of these are still missing:

- 业务目标不清
- 执行目标与职责不清
- 当前执行方案不清
- 缺少真实 benchmark case
- 缺少期望输出
- 缺少评分维度

If one real run review has already been executed, also do not finalize if any of these are still true:

- `execution-playbook.md` 的 `输入` 仍含 `待确认` 或半确认条目
- `execution-playbook.md` 的 `输出` 仍含 `待确认` 或半确认条目
- `execution-playbook.md` 的 `当前执行方案` 仍含 `待确认` 或半确认条目
- `execution-playbook.md` 仍保留 `来自真实 run 观察`、`真实 run 复核记录` 这类历史附加层

`真实 run 复核` 不属于阻断条件。即使未执行，只要 baseline 已 usable，仍可完成 init。

Continue asking for the smallest missing piece until the baseline is usable.
