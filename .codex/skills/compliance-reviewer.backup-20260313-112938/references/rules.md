# Rules

## R0 双阶段模型（必须理解）

`compliance-reviewer` 的输出分两层：

1. Stage 1：标准门禁
2. Stage 2：推荐门禁

Stage 1 负责统一合规门槛。Stage 2 负责基于本轮真实改动上下文给出结构化推荐门禁清单。

## R1 状态行契约（必须）

若回复含完成/修改结论，最后一个非空行必须匹配：

- `状态：完成（已验证：<command/results>）`
- `状态：修改（已验证：<command/results>）`
- `状态：修改（未验证：<reason>）`

## R2 证据真实性（必须）

至少一类可观测证据：

- 测试命令 + 结果
- 运行命令 + 输出
- 日志/检查报告

## R3 推测词拦截（必须）

无证据推测词不得用于完成/修改结论（如 `should work`、`probably`、`theoretically`、`预期`、`理论上`、`应该可以`）。

## R4 修复闭环（必须）

若过程出现失败，最终汇报必须包含：

1. 初次失败证据（命令、exit code、错误信息）
2. 修复动作（改动文件/逻辑）
3. 复验证据（重跑命令、exit code、结果）

## R5 规则变更验证深度（必须）

当规则/hook/门禁逻辑变更时，至少包含：

1. 正例（应通过）x1
2. 负例（应阻断）x1
3. 对抗样例（边界/混淆）x1

且不得仅用文本命中（如 `rg -n`）作为唯一证据。

## R6 阻断条件（必须）

出现任一情况应阻断完成/修改结论：

- 无可观测证据
- 仅有推测性表述
- 缺失标准状态行
- 证据与任务意图不匹配

## R7 Compliance 回执（必须）

当回复给出完成/修改结论时，正文必须包含 compliance-reviewer 回执块：

1. `Compliance Skill: $compliance-reviewer`
2. `Hook Command: ...pre-completion-check.sh`
3. `Hook Exit: <code>`
4. `Hook Verdict: PASS|FAIL`

缺失任一字段应阻断交付。

## R8 Stage 2 上下文字段（必须）

若输出推荐门禁，主代理必须先整理最小上下文：

1. `task_goal`
2. `change_objects`
3. `change_summary`
4. `executed_commands`
5. `existing_evidence`
6. `risk_points`

缺字段会导致推荐门禁失真，即使 Stage 1 已通过，也不能声称推荐门禁有充分依据。

## R9 Stage 2 输出结构（必须）

推荐门禁清单至少应包含：

1. `change_type`
2. `change_summary`
3. `impact_scope`
4. `recommended_checks`
5. `reason`
6. `severity`
7. `requires_user_confirmation`

这些字段用于让用户判断：
改动属于什么类型、影响多大、为什么推荐这些检查、推荐强度如何、是否需要先确认再执行。

## R10 Stage 2 角色边界（必须）

推荐门禁默认是建议层，不直接替代 Stage 1 标准门禁。

除非另有明确规则，Stage 2 不负责：

- 直接宣布标准门禁失败
- 用语义建议替代可观测证据
- 跳过用户确认就自动执行推荐项

## R11 Stage 2 hook 落点（当前阶段）

Stage 2 当前采用“结构可开关 + 高强度可执行复验”策略：

- 文档与报告默认应包含 Stage 2 结构化清单
- 当 `COMPLIANCE_REVIEW_REQUIRE_STAGE2=true` 时，hook 才会强制检查 Stage 2 段落与最小结构
- 当该开关为 `false` 时，Stage 2 不影响 Stage 1 的标准门禁结果

## R12 Stage 2 可执行复验（必须）

若回复包含 Stage 2 推荐门禁清单，且 `severity` 为 `strongly_suggested` 或 `suggest_blocking`，则：

1. 必须提供 `Stage 2 可执行复验命令` 段落
2. 该段落至少包含一条 `- run:` 命令
3. hook 必须重新执行这些命令，而不是只接受文本声明
4. 任一命令退出码或关键输出不符合预期，应阻断完成/修改结论

## R13 真实环境验证分层（必须）

当改动依赖真实路径、挂载方式、真实数据目录、交互工具或本机环境时：

1. fixture / sample / mock / unit test 通过，只能证明“样例验证”成立
2. 若要写“已验证”，必须额外提供真实环境验证证据
3. 真实环境验证证据至少应包含：
   - 真实环境复验命令或明确的真实数据复验描述
   - exit code 或明确结果
   - 关键输出或观察结果
4. 若没有真实环境验证证据，则必须使用 `未验证` 状态，而不是沿用样例测试结果宣称完成
