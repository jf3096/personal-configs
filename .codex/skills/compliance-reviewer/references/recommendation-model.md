# Recommendation Gate Model

## Purpose

Define the MVP mapping from real change context to Stage 2 recommendation-gate output.

## Sensitive Change Types

- `hook`
- `rule`
- `skill`
- `validator_script`
- `template`

All other values normalize to `other`.

## Impact Scopes

- `local`
- `cross-task`
- `global-verdict-changing`

Unknown values normalize to `local`.

## Severity Mapping

- non-sensitive + `local` -> `suggested`
- sensitive + `local` -> `strongly_suggested`
- sensitive + `cross-task` -> `suggest_blocking`
- sensitive + `global-verdict-changing` -> `suggest_blocking`

## Recommended Checks

Allowed MVP values:

- `positive_case`
- `negative_case`
- `adversarial_case`

Mapping:

- `suggest_blocking` -> all three checks
- sensitive + non-blocking -> `positive_case`, `negative_case`
- non-sensitive + local -> `positive_case`

## Output Contract

The generator should return:

- `change_type`
- `change_summary`
- `impact_scope`
- `recommended_checks`
- `reason`
- `severity`
- `requires_user_confirmation`

`requires_user_confirmation` stays `true` for all Stage 2 outputs in MVP.
