import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('SKILL contract includes required Chinese mode keywords', async () => {
  const text = await readFile('../../.codex/skills/workflow-graph/SKILL.md', 'utf8');
  assert.match(text, /简版/);
  assert.match(text, /详细版/);
  assert.match(text, /用户未声明时.*自动判断/s);
  assert.match(text, /\[LOOP Lx -> \(n\)\]/);
  assert.match(text, /默认只输出图/);
});

test('README links usage guide', async () => {
  const text = await readFile('README.md', 'utf8');
  assert.match(text, /docs\/usage\/workflow-graph-skill\.md/);
});
