---
name: skill-evolver
description: "Build and run a rehearsal-to-evolution loop for any target skill or workflow. Use when you need continuous improvement with explicit stages: (1) ask for rehearsal method/steps, expected outcomes, and real execution commands, (2) perform rehearsal planning, (3) execute real changes, (4) compare rehearsal vs actual results, (5) evolve rules/prompts/tests, and (6) rerun step 1 under the improved baseline."
---

# Skill Evolver

Run a repeatable improvement loop that turns ad-hoc prompt tuning into evidence-backed iteration.

## Mandatory Intake (ask first)

Before changing files, ask and lock these inputs:

1. Rehearsal method and stage order.
2. Expected outcomes and acceptance criteria.
3. Real execution commands for source/target validation.
4. Evidence format required in final report.
5. Scope of evolution: which files can be updated (for example `AGENTS.md`, target `SKILL.md`, tests).

Use this intake checklist: `references/intake-checklist.md`.

## Decision-Complete Loop

Follow this sequence exactly:

1. Define requirement: create `REQ-*.md` with scope, acceptance criteria, and evidence plan.
2. Rehearse: create `REHEARSAL-*.md` with predicted steps, risks, and validation matrix.
3. Execute for real: perform actual edits and run commands.
4. Compare: create `POSTMORTEM-*.md` with rehearsal vs actual deltas.
5. Evolve: update rules/prompts/tests based on delta findings.
6. Rerun step 1: create `REQ-*-R2.md` with tighter criteria and re-run critical checks.

Use the template guide: `references/template-guide.md`.
For multi-version derivation, use: `references/variant-playbook.md`.

## Validation Depth Baseline

Do not accept text-only checks as sole evidence.

For rule or gate changes, include at least:

1. One positive case (should pass).
2. One negative case (should block).
3. One adversarial or boundary case.

Use this evidence checklist: `references/evidence-checklist.md`.

## Scripted Bootstrap

Use `scripts/init_evolution_cycle.sh` to scaffold cycle documents quickly.

Example:

```bash
scripts/init_evolution_cycle.sh \
  --req-id REQ-101 \
  --task "Convert compliance-review-demo.js to python" \
  --source-file compliance-review-demo.js \
  --target-file compliance-review-demo.py
```

The script creates:

- `docs/REQ-<id>.md`
- `docs/REHEARSAL-<id>.md`
- `docs/POSTMORTEM-<id>.md`
- `docs/REQ-<id>-R2.md`

To derive multiple validation variants (`V1..V4`) from one base scenario, use:

```bash
scripts/generate_validation_variants.sh --req-id REQ-101 --docs-dir docs
```

## Output Contract

When reporting completion or modification, include concrete command evidence and the standard status line required by the active compliance gate.
