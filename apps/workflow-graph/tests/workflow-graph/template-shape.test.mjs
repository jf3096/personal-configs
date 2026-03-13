import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('compact template has node-line explanation format', async () => {
  const text = await readFile('../../.codex/skills/workflow-graph/templates/compact-tree.template.md', 'utf8');
  assert.match(text, /\(1\).*::/);
  assert.doesNotMatch(text, /\[1\.1\]/);
});

test('detailed template includes sub-points and loop reference', async () => {
  const text = await readFile('../../.codex/skills/workflow-graph/templates/detailed-tree.template.md', 'utf8');
  assert.match(text, /\[1\.1\]/);
  assert.match(text, /\[LOOP L1 -> \(1\)\]/);
});
