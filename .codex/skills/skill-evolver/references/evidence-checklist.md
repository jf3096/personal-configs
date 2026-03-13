# Evidence Checklist

For each loop run, collect:

1. Requirement artifacts: `REQ-*` and `REHEARSAL-*` files.
2. Actual execution proof: commands, exit codes, and key output snippets.
3. Delta proof: `POSTMORTEM-*` with prediction vs actual differences.
4. Evolution proof: changed rule/prompt/test files and rationale.
5. Rerun proof: `REQ-*-R2` plus rerun command results.

For gate/rule changes, include at least:

- Positive case (pass)
- Negative case (block)
- Adversarial/boundary case
