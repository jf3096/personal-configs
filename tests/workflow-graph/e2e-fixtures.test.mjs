import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { validateDiagram } from '../../scripts/validate-workflow-graph-skill.mjs';

async function check(file, mode) {
  const text = await readFile(file, 'utf8');
  const result = validateDiagram(text, mode);
  assert.equal(result.ok, true, `${file} invalid: ${result.reason}`);
}

test('gitlab compact fixture is valid', async () => {
  await check('tests/workflow-graph/fixtures/gitlab-compact.txt', '简版');
});

test('code structure detailed fixture is valid', async () => {
  await check('tests/workflow-graph/fixtures/code-structure-detailed.txt', '详细版');
});

test('skill runtime detailed fixture is valid', async () => {
  await check('tests/workflow-graph/fixtures/skill-runtime-detailed.txt', '详细版');
});
