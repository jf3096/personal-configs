# Workflow Graph Skill Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a reusable Codex skill that turns workflow/mechanism descriptions into tree decision diagrams with two Chinese modes (`简版`/`详细版`) and automatic mode selection when users do not specify.

**Architecture:** The implementation is split into four layers: skill contract (`SKILL.md`), rendering templates, deterministic validation script, and fixture-based tests. TDD drives each layer so output structure stays stable: tree body first, per-node single-line explanation (`::`), optional sub-points for `详细版`, and loop references (`[LOOP Lx -> (n)]`).

**Tech Stack:** Markdown skill files, Node.js (`node:test`), plain JavaScript (ESM), shell-based verification.

---

### Task 1: Bootstrap skill workspace and test harness

**Files:**
- Create: `package.json`
- Create: `skills/workflow-graph/.gitkeep`
- Create: `tests/workflow-graph/.gitkeep`
- Test: `node --test`

**Step 1: Write the failing test**

```bash
node --test
```

Expected: FAIL because no test files/harness exist yet.

**Step 2: Run test to verify it fails**

Run: `node --test`
Expected: non-zero exit code.

**Step 3: Write minimal implementation**

`package.json`
```json
{
  "name": "workflow-graph-skill",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "node --test",
    "verify:skill": "node scripts/validate-workflow-graph-skill.mjs"
  }
}
```

**Step 4: Run test to verify baseline is runnable**

Run: `npm test`
Expected: PASS (0 tests) or PASS summary with exit code 0.

**Step 5: Commit**

```bash
git add package.json skills/workflow-graph/.gitkeep tests/workflow-graph/.gitkeep
git commit -m "chore: bootstrap workflow-graph skill workspace"
```

### Task 2: Define skill contract (`简版`/`详细版` + auto mode)

**Files:**
- Create: `skills/workflow-graph/SKILL.md`
- Create: `tests/workflow-graph/skill-contract.test.mjs`
- Test: `tests/workflow-graph/skill-contract.test.mjs`

**Step 1: Write the failing test**

`tests/workflow-graph/skill-contract.test.mjs`
```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('SKILL contract includes required Chinese mode keywords', async () => {
  const text = await readFile('skills/workflow-graph/SKILL.md', 'utf8');
  assert.match(text, /简版/);
  assert.match(text, /详细版/);
  assert.match(text, /用户未声明时.*自动判断/);
  assert.match(text, /\[LOOP Lx -> \(n\)\]/);
});
```

**Step 2: Run test to verify it fails**

Run: `node --test tests/workflow-graph/skill-contract.test.mjs`
Expected: FAIL (`ENOENT` for missing `SKILL.md`).

**Step 3: Write minimal implementation**

`skills/workflow-graph/SKILL.md` must include:
- Purpose and supported scenarios (GitLab repo summary / code structure / skill mechanism)
- Output structure: tree diagram + `::` line explanation
- Mode rules: `简版`, `详细版`
- Auto decision when mode unspecified
- Loop syntax contract: `[LOOP Lx -> (n)]`
- Response rule: no extra bullet summary after diagram unless user asks

**Step 4: Run test to verify it passes**

Run: `node --test tests/workflow-graph/skill-contract.test.mjs`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/workflow-graph/SKILL.md tests/workflow-graph/skill-contract.test.mjs
git commit -m "feat: define workflow-graph skill contract and mode policy"
```

### Task 3: Add compact/detailed rendering templates

**Files:**
- Create: `skills/workflow-graph/templates/compact-tree.template.md`
- Create: `skills/workflow-graph/templates/detailed-tree.template.md`
- Create: `tests/workflow-graph/template-shape.test.mjs`
- Test: `tests/workflow-graph/template-shape.test.mjs`

**Step 1: Write the failing test**

`tests/workflow-graph/template-shape.test.mjs`
```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

test('compact template has node-line explanation format', async () => {
  const text = await readFile('skills/workflow-graph/templates/compact-tree.template.md', 'utf8');
  assert.match(text, /\(1\).*::/);
  assert.doesNotMatch(text, /\[1\.1\]/);
});

test('detailed template includes sub-points and loop reference', async () => {
  const text = await readFile('skills/workflow-graph/templates/detailed-tree.template.md', 'utf8');
  assert.match(text, /\[1\.1\]/);
  assert.match(text, /\[LOOP L1 -> \(1\)\]/);
});
```

**Step 2: Run test to verify it fails**

Run: `node --test tests/workflow-graph/template-shape.test.mjs`
Expected: FAIL because templates do not exist.

**Step 3: Write minimal implementation**

- `compact-tree.template.md`: only tree nodes with `::`.
- `detailed-tree.template.md`: same tree plus sub-points (`[n.m]`) and loop reference examples.

**Step 4: Run test to verify it passes**

Run: `node --test tests/workflow-graph/template-shape.test.mjs`
Expected: PASS.

**Step 5: Commit**

```bash
git add skills/workflow-graph/templates tests/workflow-graph/template-shape.test.mjs
git commit -m "feat: add compact and detailed tree templates"
```

### Task 4: Implement deterministic validator for generated diagrams

**Files:**
- Create: `scripts/validate-workflow-graph-skill.mjs`
- Create: `tests/workflow-graph/validator.test.mjs`
- Test: `tests/workflow-graph/validator.test.mjs`

**Step 1: Write the failing test**

`tests/workflow-graph/validator.test.mjs`
```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { validateDiagram } from '../../scripts/validate-workflow-graph-skill.mjs';

test('compact diagram passes contract checks', () => {
  const sample = '(1) 接收任务描述 :: 说明\n└─ (2) 信息是否完整? :: 校验\n   └─ No -> [LOOP L1 -> (1)]';
  const result = validateDiagram(sample, '简版');
  assert.equal(result.ok, true);
});

test('detailed diagram requires sub-points', () => {
  const sample = '(1) 接收任务描述 :: 说明';
  const result = validateDiagram(sample, '详细版');
  assert.equal(result.ok, false);
});
```

**Step 2: Run test to verify it fails**

Run: `node --test tests/workflow-graph/validator.test.mjs`
Expected: FAIL because validator module is missing.

**Step 3: Write minimal implementation**

`scripts/validate-workflow-graph-skill.mjs`
```js
export function validateDiagram(text, mode) {
  const hasNodeLine = /\(\d+\).*::/.test(text);
  const hasLoop = /\[LOOP\s+L\d+\s+->\s+\(\d+\)\]/.test(text);
  const hasSubPoint = /\[\d+\.\d+\]/.test(text);

  if (!hasNodeLine) return { ok: false, reason: 'missing node explanation line (::)' };
  if (mode === '详细版' && !hasSubPoint) return { ok: false, reason: 'detailed mode requires sub-points' };
  if (mode === '简版' && hasSubPoint) return { ok: false, reason: 'compact mode should not contain sub-points' };

  return { ok: true, reason: hasLoop ? 'ok_with_loop' : 'ok_without_loop' };
}

if (process.argv[1]?.endsWith('validate-workflow-graph-skill.mjs')) {
  const mode = process.argv[2] || '简版';
  const input = process.argv[3] || '';
  const result = validateDiagram(input, mode);
  console.log(JSON.stringify(result));
  process.exit(result.ok ? 0 : 1);
}
```

**Step 4: Run test to verify it passes**

Run: `node --test tests/workflow-graph/validator.test.mjs`
Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/validate-workflow-graph-skill.mjs tests/workflow-graph/validator.test.mjs
git commit -m "feat: add diagram contract validator"
```

### Task 5: Add end-to-end fixtures for three target scenarios

**Files:**
- Create: `tests/workflow-graph/fixtures/gitlab-compact.txt`
- Create: `tests/workflow-graph/fixtures/code-structure-detailed.txt`
- Create: `tests/workflow-graph/fixtures/skill-runtime-detailed.txt`
- Create: `tests/workflow-graph/e2e-fixtures.test.mjs`
- Test: `tests/workflow-graph/e2e-fixtures.test.mjs`

**Step 1: Write the failing test**

`tests/workflow-graph/e2e-fixtures.test.mjs`
```js
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
```

**Step 2: Run test to verify it fails**

Run: `node --test tests/workflow-graph/e2e-fixtures.test.mjs`
Expected: FAIL because fixture files do not exist.

**Step 3: Write minimal implementation**

Create three fixture outputs using the final style contract:
- `gitlab-compact.txt`: no sub-points.
- `code-structure-detailed.txt`: full key nodes + sub-points.
- `skill-runtime-detailed.txt`: full key nodes + sub-points + at least one loop.

**Step 4: Run test to verify it passes**

Run: `node --test tests/workflow-graph/e2e-fixtures.test.mjs`
Expected: PASS.

**Step 5: Commit**

```bash
git add tests/workflow-graph/fixtures tests/workflow-graph/e2e-fixtures.test.mjs
git commit -m "test: add e2e fixtures for workflow-graph scenarios"
```

### Task 6: Final verification and usage documentation

**Files:**
- Create: `docs/usage/workflow-graph-skill.md`
- Modify: `README.md`
- Test: full suite

**Step 1: Write the failing test**

Add an assertion in `tests/workflow-graph/skill-contract.test.mjs` that README links usage doc:
```js
test('README links usage guide', async () => {
  const text = await readFile('README.md', 'utf8');
  assert.match(text, /docs\/usage\/workflow-graph-skill\.md/);
});
```

**Step 2: Run test to verify it fails**

Run: `npm test`
Expected: FAIL because README does not contain usage link.

**Step 3: Write minimal implementation**

- Create `docs/usage/workflow-graph-skill.md` with:
  - trigger phrases
  - mode behavior (`简版`/`详细版`/auto)
  - one compact sample and one detailed sample
- Update `README.md` to link design + implementation + usage docs.

**Step 4: Run test to verify it passes**

Run: `npm test`
Expected: PASS all tests.

Run: `npm run verify:skill -- 简版 "(1) 接收任务描述 :: 说明"`
Expected: JSON output and exit code consistent with validation.

**Step 5: Commit**

```bash
git add README.md docs/usage/workflow-graph-skill.md tests/workflow-graph/skill-contract.test.mjs
git commit -m "docs: add workflow-graph usage guide and final verification"
```

## Verification Checklist (Execution Phase)
- Run `npm test`
- Run `npm run verify:skill -- 简版 "<sample>"`
- Run `npm run verify:skill -- 详细版 "<sample>"`
- Manual read check: output is “diagram-first” without forced trailing bullet summary.

## Skills to Apply During Execution
- `@test-driven-development` before each implementation slice
- `@verification-before-completion` before any “完成/修改” statement
- `@requesting-code-review` after Task 6 if preparing for merge

