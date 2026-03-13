# Ralph Loop Example Prompt

Use the files in the current workspace as the source of truth:
- `prd.md`
- `execution-playbook.md`
- `benchmark.md`

Task:
1. Read the baseline files.
2. Execute the current plan in the workspace.
3. If the run fails, use the failure as data and improve the files or outputs.
4. Re-run until the benchmark is satisfied.

Stop condition:
- Only output `<promise>DONE</promise>` when the benchmark's through-standard is genuinely satisfied.
- Include one `<iteration_report>...</iteration_report>` block in each final message with:
  - before vs after changes
  - optimization strategy
  - score_before / score_after / score_delta
  - next iteration plan

Safety:
- If you are still blocked near the iteration limit, document the blocker in files instead of lying with a false promise.
