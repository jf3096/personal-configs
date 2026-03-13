# Rules

## R0 双层判定模型（必须）

`compliance-reviewer` 必须输出双层判定：

1. `Compliance Verdict: PASS|FAIL`
2. `Delivery Verdict: PASS|PASS_WITH_HIGH_RISK|BLOCKED`

`Compliance` 与 `Delivery` 语义不同，不可互相替代。

## R1 状态行契约（必须）

若回复含完成/修改结论，最后一个非空行必须匹配：

- `状态：完成（已验证：<command/results>）`
- `状态：修改（已验证：<command/results>）`
- `状态：修改（未验证：<reason>）`

## R2 证据真实性（必须）

至少提供可观测证据：

- command
- result（含关键输出）
- exit code（或等价退出码信息）

## R3 推测词拦截（必须）

无证据推测词不得用于完成/修改结论（如 `should work`、`probably`、`theoretically`、`预期`、`理论上`、`应该可以`）。

## R4 失败闭环（必须）

若过程出现失败，最终汇报必须包含：

1. 初次失败证据（命令、exit code、错误信息）
2. 修复动作（改动文件/逻辑）
3. 复验证据（重跑命令、exit code、结果）

## R5 高风险触发（必须）

命中以下任一条件视为高风险：

1. 新增依赖、DB migration、公共 API/协议变更、生产权限/配置脚本变更。
2. `files_changed > 5`
3. `line_delta > 200`

## R6 高风险判定约束（必须）

高风险路径下：

1. 禁止 `Delivery Verdict: PASS`
2. 允许 `PASS_WITH_HIGH_RISK` 或 `BLOCKED`
3. `Release Advice` 必须为 `Hold`

## R7 高风险强制 TDD 复测（必须）

高风险路径必须提供：

1. `TDD-Strict Revalidation` 段落
2. `TDD Revalidation Command: <cli command>`

hook 必须实际执行该命令并检查 JSON 契约字段：

- `revalidation_status`
- `test_evidence`
- `run_evidence`

## R8 TDD CLI 失败语义（必须）

若 TDD CLI 调用失败（命令失败、超时、非 JSON、字段非法）：

1. 只允许 `Delivery Verdict: BLOCKED`
2. 声称 `PASS_WITH_HIGH_RISK` 必须阻断

## R9 Stage 2 可执行复验（必须）

若回复包含 Stage 2 推荐清单，且 `severity` 为 `strongly_suggested` 或 `suggest_blocking`，则必须提供 `Stage 2 可执行复验命令` 并由 hook 重跑。

## R10 Compliance 回执（必须）

当回复给出完成/修改结论时，正文必须包含：

1. `Compliance Skill: $compliance-reviewer`
2. `Hook Command: ...pre-completion-check.sh`
3. `Hook Exit: <code>`
4. `Hook Verdict: PASS|FAIL`

## R11 自动修复尝试上限（必须）

若报告提供 `Auto Remediation Attempts` 字段，数值不得超过 `2`。

## R12 真实环境验证分层（必须）

当改动依赖真实路径、挂载方式、真实数据目录、交互工具或本机环境时：

1. fixture/sample/mock/unit test 通过，只能证明样例验证
2. 若写“已验证”，必须补充真实环境验证证据
3. 缺真实环境证据时，应使用 `未验证` 或 `Delivery Verdict: BLOCKED`
