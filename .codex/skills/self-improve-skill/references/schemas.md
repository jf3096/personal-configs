# Self Improve Schemas

## loop-config.json

```json
{
  "summary_a_name": "self-improve-skill-bootstrap",
  "max_loops": 3,
  "target_score": 85,
  "execute_cmd": "npm run test",
  "score_cmd": "node scripts/score.js",
  "quality_cmd": "npm run lint",
  "created_at": "2026-03-04T00:00:00Z"
}
```

## iteration.json

```json
{
  "iteration": 1,
  "started_at": "2026-03-04T00:00:00Z",
  "ended_at": "2026-03-04T00:02:00Z",
  "execute_exit": 0,
  "score_exit": 0,
  "quality_exit": 0,
  "score": 88.5,
  "target_score": 85,
  "passed": true,
  "artifacts": {
    "execute_stdout": "execute.stdout.log",
    "execute_stderr": "execute.stderr.log",
    "score_stdout": "score.stdout.log",
    "score_stderr": "score.stderr.log",
    "quality_stdout": "quality.stdout.log",
    "quality_stderr": "quality.stderr.log"
  }
}
```

## run-summary.json

```json
{
  "summary_a_name": "self-improve-skill-bootstrap",
  "max_loops": 3,
  "target_score": 85,
  "pass": true,
  "iterations_used": 2,
  "history": [
    {"iteration": 1, "score": 80.0, "passed": false},
    {"iteration": 2, "score": 88.5, "passed": true}
  ]
}
```
