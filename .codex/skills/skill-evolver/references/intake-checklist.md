# Intake Checklist

Ask and lock these fields before execution:

1. `rehearsal_steps`: Stage order the user wants.
2. `expected_outcomes`: Observable success criteria.
3. `execution_commands`: Real commands to validate actual behavior.
4. `evidence_format`: Required proof format (exit code, output snippets, artifacts).
5. `evolution_scope`: Which files/rules/tests can be changed.
6. `rerun_scope`: Which checks must be rerun after evolution.

If any field is missing, ask before mutating files.
