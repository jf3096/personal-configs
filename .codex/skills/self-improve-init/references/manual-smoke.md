# Manual Smoke Test

## Sample Prompt A
我已经知道 baseline 大概要怎么做了，帮我落成 prd、execution-playbook、benchmark。

## Sample Prompt B
我只想拿到 bilibili.com 热搜榜结果，但我并不知道 baseline 该怎么设计，请你帮我起草一版。

## Expected Questions
- 首轮给出两个模式选项：`自述 baseline` / `含糊 baseline 创作模式`
- 如果用户选择 `自述 baseline`，以用户自述为主，必要时轻量使用 `brainstorming`
- 如果用户选择 `含糊 baseline 创作模式`，先收集用户想要的结果，再用 `brainstorming`，必要时使用 web research / research 起草推荐 baseline
- AI 起草后，必须让用户确认、修改或否决该推荐 baseline 草案
- 在草案确认前，不得转去追问 `workspace` 或其他后续缺失项
- 在起草草案时，应区分高层执行骨架与候选执行策略
- workspace 路径是什么
- 真实 benchmark case 是什么
- 执行职责 / 运行方式是什么
- 期望输出和评分维度是什么
- baseline 可用后，是否要做一次真实 run 复核

## Expected Outputs
- 在确认 `workspace` 后立即创建 draft baseline
- 未确认字段写为 `待确认`
- 每轮汇报当前阶段、已确认项、缺失项、是否已落盘
- `含糊 baseline 创作模式` 中应明确标记“推荐 baseline 草案”
- `含糊 baseline 创作模式` 中应明确标记 `草案状态：待用户确认 | 已确认 | 已修改后确认`
- 当 `草案状态` 为 `待用户确认` 时，本轮唯一问题只能是确认 / 修改 / 重起该草案
- 当主题依赖当前外部事实时，应使用 research 补足关键事实后再起草
- 在用户确认草案前，不得直接把草案写成最终 baseline
- 真实 run 复核是可选项，不阻断 baseline
- 如果用户未准备好，必须明确跳过真实 run 并记录原因
- `prd.md` 应聚焦稳定任务定义与高层执行路径
- `execution-playbook.md` 应聚焦执行职责、运行方式、候选策略与降级路径
- `benchmark.md` 应聚焦 benchmark case、期望输出、评分维度与通过标准
- `<workspace>/prd.md`
- `<workspace>/execution-playbook.md`
- `<workspace>/benchmark.md`
- 如果用户明确同意且条件具备，可额外写入 `<workspace>/evidence/`
