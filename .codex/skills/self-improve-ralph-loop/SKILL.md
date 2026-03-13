---
name: self-improve:ralph-loop
description: Use when you want Ralph-style repeated Codex iterations on the same prompt until a completion promise or iteration limit stops the run.
---

# Self Improve Ralph Loop

## Overview

`self-improve:ralph-loop` is a Codex-native sibling to `self-improve:init`.

It preserves the Ralph idea:
- keep the prompt stable
- let file changes accumulate between iterations
- stop only on a completion promise, cancellation, or iteration limit

Unlike Claude's upstream `ralph-loop` plugin, this version runs through a CLI wrapper around `codex exec`, because Codex CLI does not support Claude plugin slash commands or stop hooks.

## When to Use

Use this when:
- you already have a baseline or prompt and want repeated Codex execution
- success criteria can be stated clearly
- the task benefits from iterative refinement
- the task can be verified through files, tests, logs, or structured outputs

Do not use this when:
- the task needs frequent human design decisions
- the completion condition is subjective
- the task is dangerous without supervision
- one-shot execution is enough

## Required Inputs

Before starting a loop, prepare:
- a stable prompt file
- a concrete completion promise
- a hard `--max-iterations` cap
- a workspace where file changes should accumulate

If you came from `self-improve:init`, your prompt should usually reference:
- `prd.md`
- `execution-playbook.md`
- `benchmark.md`

## Core Commands

Start a loop:

```bash
python3 .codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py start \
  --workspace /abs/path/to/workspace \
  --prompt-file /abs/path/to/prompt.md \
  --run-root temp/ralph-loop-runs \
  --completion-promise "DONE" \
  --max-iterations 10
```

Disable the per-iteration report contract only when you intentionally want free-form output:

```bash
python3 .codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py start \
  --workspace /abs/path/to/workspace \
  --prompt-file /abs/path/to/prompt.md \
  --run-root temp/ralph-loop-runs \
  --completion-promise "DONE" \
  --max-iterations 10 \
  --disable-iteration-report
```

Check status:

```bash
python3 .codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py status \
  /abs/path/to/run-dir
```

Resume:

```bash
python3 .codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py resume \
  /abs/path/to/run-dir
```

Cancel:

```bash
python3 .codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py cancel \
  /abs/path/to/run-dir
```

Start a todo-driven loop:

```bash
python3 .codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py todo-start \
  --workspace /abs/path/to/workspace \
  --cases-root /abs/path/to/workspace/cases \
  --todo-file /abs/path/to/workspace/todo.yaml \
  --run-root temp/ralph-loop-runs
```

Todo status:

```bash
python3 .codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py todo-status \
  /abs/path/to/todo-run-dir --json
```

Todo resume:

```bash
python3 .codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py todo-resume \
  /abs/path/to/todo-run-dir
```

Todo cancel:

```bash
python3 .codex/skills/self-improve-ralph-loop/scripts/ralph_loop.py todo-cancel \
  /abs/path/to/todo-run-dir
```

Run the bundled smoke test:

```bash
bash .codex/skills/self-improve-ralph-loop/scripts/run-smoke.sh
```

Run the todo smoke test:

```bash
bash .codex/skills/self-improve-ralph-loop/scripts/run-todo-smoke.sh
```

## Completion Promise Rules

- Prefer one short phrase such as `DONE`
- require exact output in the prompt: `<promise>DONE</promise>`
- do not use vague promises
- always pair with `--max-iterations`
- with default settings, completion promise is accepted only when the iteration report contract is also valid

## Iteration Reporting Contract (Default ON)

By default, each iteration must include a structured report block in the final model message:

```text
<iteration_report>
iteration: <n>
changes_before: ...
changes_after: ...
optimization_strategy: ...
score_before: <0-100>/100
score_after: <0-100>/100
score_delta: <after-before>
next_iteration_plan: ...
</iteration_report>
```

What this gives you per iteration:
- before/after change summary
- optimization idea and strategy rationale
- score comparison (`score_before` vs `score_after`)
- next-step plan

If the report block is missing or malformed, the wrapper will not accept completion promise for that iteration.

## Todo Mode Files

Todo mode uses three file types:

1. `cases/catalog.yaml`
- defines the full case registry (`id/title/type/spec_file/priority/enabled`)

2. `cases/<case-id>.md`
- natural-language case spec with objective, steps, expected outcomes, evidence, and failure signals

3. `todo.yaml`
- execution plan (`todo_id`, `loop_rounds`, `continue_on_failure`, `selection_policy`, `items`)

Reference examples:

- `.codex/skills/self-improve-ralph-loop/references/todo-catalog.example.yaml`
- `.codex/skills/self-improve-ralph-loop/references/todo.example.yaml`
- `.codex/skills/self-improve-ralph-loop/references/cases/case-positive-example.md`
- `.codex/skills/self-improve-ralph-loop/references/cases/case-negative-example.md`

## Case Reporting Contract (Todo Mode)

Each case attempt final message must include one `<case_report>...</case_report>` block:

```text
<case_report>
case_id: <id>
verdict: <pass|fail>
expectation_check: <met|not_met>
failure_signal_check: <hit|not_hit>
evidence_refs: <path1,path2>
confidence: <0-100>
next_action: <continue|stop|retry>
</case_report>
```

Validation uses three layers:

1. semantics (`positive` vs `negative`)
2. evidence (`evidence_refs` exists, non-empty, inside workspace)
3. optional quality checks (`quality_checks` commands all exit 0)

For `positive` cases, default stability is strict `3/3`:
- `stability_runs = 3`
- `stability_pass_threshold = 3`

## Artifacts

Each run writes:
- `prompt.md`
- `state.json`
- `summary.md`
- `iterations/iteration-*.prompt.md`
- `iterations/iteration-*.stdout.log`
- `iterations/iteration-*.stderr.log`
- `iterations/iteration-*.last-message.txt`
- `iterations/iteration-*.report.md`

Each todo run writes:
- `todo.snapshot.yaml`
- `state.json`
- `summary.md`
- `scoreboard.json`
- `progress.txt`
- `items/<case-id>/attempt-*/prompt.md`
- `items/<case-id>/attempt-*/stdout.log`
- `items/<case-id>/attempt-*/stderr.log`
- `items/<case-id>/attempt-*/last-message.txt`
- `items/<case-id>/attempt-*/report.md`

## Suggested Pattern With self-improve:init

1. Use `self-improve:init` to produce a baseline.
2. Write a loop prompt that references the baseline files and expected completion promise.
3. Start `self-improve:ralph-loop` on that workspace.
4. Inspect `summary.md`, iteration logs, and output files.
5. Use the latest files as the next stable baseline.
