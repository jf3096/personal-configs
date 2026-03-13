# Evidence Checklist

## 证据契约分层

1. **Compliance 证据**
证明汇报结构、回执与规则满足门禁要求。
2. **Delivery 证据**
证明任务目标真实达成，而非推导达成。

## 最低证据（三件套）

每个关键结论至少给出：

1. `command`
2. `result`（关键输出）
3. `exit code`

## 双 verdict 必备证据

1. `Compliance Verdict`
2. `Delivery Verdict`
3. `Release Advice`

## 高风险路径附加证据

1. 高风险触发依据（类型或阈值）
2. `TDD-Strict Revalidation` 段落
3. `TDD Revalidation Command`
4. CLI JSON 输出字段：
   - `revalidation_status`
   - `test_evidence`
   - `run_evidence`

## Stage 2 推荐依据

1. `task_goal`
2. `change_objects`
3. `change_summary`
4. `executed_commands`
5. `existing_evidence`
6. `risk_points`

## 失败闭环证据

若曾失败，必须按时间顺序给出：

1. 初次失败（命令 + exit + 错误）
2. 修复动作（改了什么）
3. 复验结果（命令 + exit + 输出）

## 反假证据规则

以下内容不能单独作为证据：

1. “应该可以”“理论上可行”等推导语句
2. 未执行命令的静态判断
3. 只给结果不提供命令与退出码
