# Report Template

## 修复闭环报告

### Stage 2 推荐门禁上下文摘要
- `task_goal`:
- `change_objects`:
- `change_summary`:
- `executed_commands`:
- `existing_evidence`:
- `risk_points`:

### Stage 2 推荐门禁清单
- `change_type`:
- `change_summary`:
- `impact_scope`:
- `recommended_checks`:
- `reason`:
- `severity`:
- `requires_user_confirmation`:

### Stage 2 可执行复验命令
- `run`:
- `expect_exit`:
- `expect_stdout`:
- `expect_stderr`:

### 初次验证失败
- 命令：
- 退出码：
- 关键错误：

### 修复动作
- 修改文件：
- 修改点：

### 复验结果
- 命令：
- 退出码：
- 关键输出：

### Compliance 回执（必填）
- Compliance Skill: `$compliance-reviewer`
- Hook Command: `cat /tmp/response-draft.txt | COMPLIANCE_REVIEW_VERBOSE=true bash .../pre-completion-check.sh`
- Hook Exit: `0|1`
- Hook Verdict: `PASS|FAIL`

### 最终状态行
- `状态：完成（已验证：...）` 或
- `状态：修改（已验证：...）` 或
- `状态：修改（未验证：...）`
