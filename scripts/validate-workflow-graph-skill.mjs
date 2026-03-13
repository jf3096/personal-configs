export function validateDiagram(text, mode) {
  const hasNodeLine = /\(\d+\).*::/.test(text);
  const hasLoop = /\[LOOP\s+L\d+\s+->\s+\(\d+\)\]/.test(text);
  const hasSubPoint = /\[\d+\.\d+\]/.test(text);

  if (!hasNodeLine) {
    return { ok: false, reason: 'missing node explanation line (::)' };
  }

  if (mode === '详细版' && !hasSubPoint) {
    return { ok: false, reason: 'detailed mode requires sub-points' };
  }

  if (mode === '简版' && hasSubPoint) {
    return { ok: false, reason: 'compact mode should not contain sub-points' };
  }

  return { ok: true, reason: hasLoop ? 'ok_with_loop' : 'ok_without_loop' };
}

if (process.argv[1]?.endsWith('validate-workflow-graph-skill.mjs')) {
  const mode = process.argv[2] || '简版';
  const input = process.argv[3] || '';
  const result = validateDiagram(input, mode);
  console.log(JSON.stringify(result));
  process.exit(result.ok ? 0 : 1);
}
