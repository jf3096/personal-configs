# Variant Playbook

Use this playbook to derive multiple validation versions from one base scenario.

## Base Scenario Template

Example base scenario:

1. Create requirement: convert `compliance-review-demo.js` to python.
2. Rehearse using `AGENTS.md` + `compliance-reviewer` rules.
3. Execute real changes.
4. Compare rehearsal vs actual and reflect.
5. Evolve rules/tests and rerun step 1.

## How to Derive Variants

Create variants by changing **one axis at a time**:

1. Validation focus axis
- behavior equivalence
- failure-closure evidence
- gate robustness
- adversarial resistance

2. Scope axis
- code-only
- rule-only
- code + rule

3. Evidence depth axis
- minimal (commands + exit)
- standard (commands + output snippets + diff)
- strict (plus positive/negative/adversarial matrix)

## Recommended Variant Set

- `V1-baseline-equivalence`
  - Keep behavior equivalent and prove with normalized diff.
- `V2-failure-closure`
  - Intentionally hit one failure, then fix and re-verify.
- `V3-gate-regression`
  - Change rules/hook and run positive/negative/adversarial + regression suite.
- `V4-adversarial-hardening`
  - Add mixed-language/format/keyword bypass probes.

## Output Contract per Variant

Each variant must produce:

1. `REQ` (variant objective and acceptance)
2. `REHEARSAL` (predicted steps and risks)
3. `POSTMORTEM` (delta and evolution actions)
4. `R2` (tightened rerun criteria)

## Anti-Pattern

Do not treat text match checks (`rg -n`) as the only evidence.
