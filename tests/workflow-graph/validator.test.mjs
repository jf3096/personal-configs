import test from 'node:test';
import assert from 'node:assert/strict';
import { validateDiagram } from '../../scripts/validate-workflow-graph-skill.mjs';

test('compact diagram passes contract checks', () => {
  const sample = '(1) 接收任务描述 :: 说明\\n└─ (2) 信息是否完整? :: 校验\\n   └─ No -> [LOOP L1 -> (1)]';
  const result = validateDiagram(sample, '简版');
  assert.equal(result.ok, true);
});

test('detailed diagram requires sub-points', () => {
  const sample = '(1) 接收任务描述 :: 说明';
  const result = validateDiagram(sample, '详细版');
  assert.equal(result.ok, false);
});

test('compact diagram rejects sub-points', () => {
  const sample = '(1) 接收任务描述 :: 说明\\n[1.1] 输入来源';
  const result = validateDiagram(sample, '简版');
  assert.equal(result.ok, false);
});
