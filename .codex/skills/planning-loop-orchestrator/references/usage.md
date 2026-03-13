# Usage Reference

## Fast Start

1. Generate choices:

```bash
bash scripts/rule-verifier/planning-loop.sh --goal "<goal>" --context "<context>"
```

2. Execute with selected choice:

```bash
bash scripts/rule-verifier/planning-loop.sh --goal "<goal>" --choice B --execute-cmd '<cmd>' --quality-cmd '<cmd>'
```

## Output Checklist

- plan/plan-options.md
- plan/selected-plan.md
- plan/progress.txt
- loop-history.tsv
- run-summary.json
