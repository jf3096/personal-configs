# Evidence Checklist

## 双阶段证据分层

证据分两层理解：

1. **Stage 1 基础证据**
用于证明交付结论本身不是空口完成。
2. **Stage 2 推荐依据**
用于证明推荐门禁不是拍脑袋，而是基于真实上下文生成。

## 最低证据

1. 执行命令（可复制）
2. 退出码（exit code）
3. 关键输出片段（命中或错误）

## 推荐补充

1. 证据文件路径（日志/输出文件）
2. 正/负/对抗样例结果
3. `Stage 2 可执行复验命令` 及其实际重跑结果
4. 归一化差异结果（若涉及跨实现比对）
5. 真实环境验证证据：
   - 真实路径 / 真实数据 / 真实交互环境的复验命令
   - exit code
   - 关键输出或肉眼观察结果
6. Hook verbose 判定输出（证明门禁确实触发）
7. Stage 2 输入摘要：
   - `task_goal`
   - `change_objects`
   - `change_summary`
   - `executed_commands`
   - `existing_evidence`
   - `risk_points`
8. Stage 2 结构化输出：
   - `change_type`
   - `change_summary`
   - `impact_scope`
   - `recommended_checks`
   - `reason`
   - `severity`
   - `requires_user_confirmation`

## 失败闭环证据

若曾失败，必须按时间顺序给出：

1. 初次失败（命令 + exit + 错误）
2. 修复动作（改了什么）
3. 复验通过（命令 + exit + 结果）
