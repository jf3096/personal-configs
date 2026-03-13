# Usage

## Step 1: 准备工作目录

```bash
mkdir -p .self-improve-skill/<summary_a_name>
```

## Step 2: 写入三份对齐文档

1. `prd.md`
2. `expectations.md`
3. `acceptance.md`

## Step 3: 启动自动迭代

```bash
bash scripts/rule-verifier/self-improve-loop.sh \
  --workspace ".self-improve-skill/<summary_a_name>" \
  --max-loops 3 \
  --target-score 85 \
  --execute-cmd 'npm run test' \
  --score-cmd 'node scripts/score.js' \
  --quality-cmd 'npm run lint'
```

## Step 4: 查看结果

1. `runs/run-*/loop-history.tsv`
2. `runs/run-*/run-summary.json`
3. `runs/run-*/iter-*/feedback.md`
