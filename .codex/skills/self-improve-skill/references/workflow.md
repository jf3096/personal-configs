# Self Improve Workflow

## 1) PRD 模板

```markdown
# PRD

## Goal
- <一句话目标>

## Background
- <业务上下文>

## Scope
- In scope:
  - <项1>
  - <项2>
- Out of scope:
  - <项A>

## Inputs / Outputs
- Inputs:
  - <输入来源>
- Outputs:
  - <输出产物>

## Constraints
- <性能/依赖/预算/时间约束>

## Risks
- <风险1>
- <风险2>

## Open Questions
- [ ] <待澄清问题>

## Clarification Log
- 2026-03-04 v0: initial draft
```

## 2) Expectations 模板

```markdown
# Expectations

## Functional
1. <功能期望1>
2. <功能期望2>

## Non-Functional
1. <时延/稳定性/成本>
2. <可维护性约束>

## Verification Hints
1. <如何验证 expectation-1>
2. <如何验证 expectation-2>

## Open Questions
- [ ] <待澄清问题>
```

## 3) Acceptance 模板

```markdown
# Acceptance

## Pass Criteria
1. <通过标准1>
2. <通过标准2>

## Score Gates
- target_score: <number>
- hard_gates:
  - <gate-1>
  - <gate-2>

## Failure Conditions
1. <失败条件1>
2. <失败条件2>

## Evidence Required
1. <日志/报告路径>
2. <关键输出路径>
```

## 4) Loop 执行文件

- `loop-config.json`: 迭代参数
- `runs/run-*/loop-history.tsv`: 每轮分数与通过状态
- `runs/run-*/iter-*/iteration.json`: 单轮执行细节
- `runs/run-*/iter-*/feedback.md`: 单轮复盘
- `runs/run-*/run-summary.json`: 全局总结
