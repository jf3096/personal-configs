#!/bin/bash
# Codex Compliance Hook
# Validate completion/modification declarations before final response

if [ "${COMPLIANCE_REVIEW_BYPASS_HOOK:-}" = "1" ]; then
  exit 0
fi

COMPLETION_KEYWORDS=(
  "任务完成"
  "已完成"
  "修复完成"
  "实现完成"
  "done"
  "finished"
  "completed"
  "task complete"
  "implementation complete"
)

MODIFICATION_KEYWORDS=(
  "已修改"
  "修改了"
  "已更新"
  "已变更"
  "updated"
  "modified"
  "changed"
)

MISSING_VERIFICATION_KEYWORDS=(
  "应该可以"
  "理论上"
  "预期"
  "估计"
  "probably"
  "theoretically"
  "should work"
  "expected to"
)

VERIFICATION_EVIDENCE_KEYWORDS=(
  "测试结果"
  "验证通过"
  "测试通过"
  "运行结果"
  "verified"
  "test result"
  "test passed"
  "verification passed"
  "output:"
  "log:"
)

ENVIRONMENT_SENSITIVE_KEYWORDS=(
  "真实 session"
  "真实路径"
  "路径挂载"
  "挂载路径"
  "真实数据"
  "~/.codex/sessions"
  "fzf 交互"
  "real session"
  "real path"
  "real data"
  "interactive fzf"
)

REAL_ENVIRONMENT_EVIDENCE_KEYWORDS=(
  "真实环境验证"
  "真实数据验证"
  "真实 session 数据执行"
  "真实 ~/.codex/sessions"
  "真实路径挂载验证"
  "real session data verified"
  "real-environment verified"
  "manual fzf check"
)

RESPONSE="${CLAUDE_RESPONSE:-$(cat)}"
REQUIRE_STANDARD_STATUS="${COMPLIANCE_REVIEW_REQUIRE_STANDARD_STATUS:-true}"
REQUIRE_COMPLIANCE_RECEIPT="${COMPLIANCE_REVIEW_REQUIRE_COMPLIANCE_RECEIPT:-true}"
REQUIRE_STAGE2="${COMPLIANCE_REVIEW_REQUIRE_STAGE2:-false}"
VERBOSE="${COMPLIANCE_REVIEW_VERBOSE:-false}"
EXECUTABLE_RECHECK_SCRIPT="/home/jf3096/.codex/skills/compliance-reviewer/scripts/executable_recheck.py"

CLAIMS_COMPLETION=false
CLAIMS_MODIFICATION=false
MISSING_VERIFICATION=false
HAS_VERIFICATION_EVIDENCE=false
HAS_ENVIRONMENT_SENSITIVE_CHANGE=false
HAS_REAL_ENVIRONMENT_EVIDENCE=false

for keyword in "${COMPLETION_KEYWORDS[@]}"; do
  if echo "$RESPONSE" | grep -qi "$keyword"; then
    CLAIMS_COMPLETION=true
    break
  fi
done

for keyword in "${MODIFICATION_KEYWORDS[@]}"; do
  if echo "$RESPONSE" | grep -qi "$keyword"; then
    CLAIMS_MODIFICATION=true
    break
  fi
done

for keyword in "${MISSING_VERIFICATION_KEYWORDS[@]}"; do
  if echo "$RESPONSE" | grep -qi "$keyword"; then
    MISSING_VERIFICATION=true
    break
  fi
done

for keyword in "${VERIFICATION_EVIDENCE_KEYWORDS[@]}"; do
  if echo "$RESPONSE" | grep -qi "$keyword"; then
    HAS_VERIFICATION_EVIDENCE=true
    break
  fi
done

for keyword in "${ENVIRONMENT_SENSITIVE_KEYWORDS[@]}"; do
  if echo "$RESPONSE" | grep -qi "$keyword"; then
    HAS_ENVIRONMENT_SENSITIVE_CHANGE=true
    break
  fi
done

for keyword in "${REAL_ENVIRONMENT_EVIDENCE_KEYWORDS[@]}"; do
  if echo "$RESPONSE" | grep -qi "$keyword"; then
    HAS_REAL_ENVIRONMENT_EVIDENCE=true
    break
  fi
done

LAST_NON_EMPTY_LINE="$(echo "$RESPONSE" | sed '/^[[:space:]]*$/d' | tail -n 1)"
STANDARD_STATUS_DECLARATION_PATTERN='^(状态[:：][[:space:]]*)?(完成|修改|修改完成|修复完成|实现完成)[[:space:]]*[(（](已验证|未验证)[:：]?[^)）]+[)）][[:space:]]*$'
UNVERIFIED_STATUS_PATTERN='[(（]未验证[:：]?[^)）]+[)）][[:space:]]*$'

HAS_STANDARD_STATUS_DECLARATION=false
if echo "$LAST_NON_EMPTY_LINE" | grep -Eq "$STANDARD_STATUS_DECLARATION_PATTERN"; then
  HAS_STANDARD_STATUS_DECLARATION=true
fi

IS_EXPLICIT_UNVERIFIED=false
if echo "$LAST_NON_EMPTY_LINE" | grep -Eq "$UNVERIFIED_STATUS_PATTERN"; then
  IS_EXPLICIT_UNVERIFIED=true
fi

STATUS_VERIFIED_PAYLOAD="$(echo "$LAST_NON_EMPTY_LINE" | sed -E 's/^.*[(（]已验证[:：]?//; s/[)）][[:space:]]*$//')"
STATUS_PAYLOAD_CLEAN="$(echo "$STATUS_VERIFIED_PAYLOAD" | sed -E 's/[[:space:]]+//g; s/[[:punct:]，。；：！？【】《》、“”‘’（）]//g')"
STATUS_PAYLOAD_HAS_RESULT=false
if echo "$STATUS_VERIFIED_PAYLOAD" | grep -Eqi '(pass|passed|通过|失败|fail|exit|输出|log|ms|耗时|error|ok|成功|拒绝|[0-9])'; then
  STATUS_PAYLOAD_HAS_RESULT=true
fi

HAS_COMPLIANCE_SKILL=false
if echo "$RESPONSE" | grep -Eqi '(\$compliance-reviewer|compliance-reviewer)'; then
  HAS_COMPLIANCE_SKILL=true
fi

HAS_COMPLIANCE_HOOK_COMMAND=false
if echo "$RESPONSE" | grep -Eqi 'pre-completion-check\.sh'; then
  HAS_COMPLIANCE_HOOK_COMMAND=true
fi

HAS_COMPLIANCE_HOOK_EXIT=false
if echo "$RESPONSE" | grep -Eqi '(Hook Exit|Compliance Exit|Compliance Hook Exit|Exit Code)[:：][[:space:]]*[0-9]+'; then
  HAS_COMPLIANCE_HOOK_EXIT=true
fi

HAS_COMPLIANCE_HOOK_VERDICT=false
if echo "$RESPONSE" | grep -Eqi '(Hook Verdict|Compliance Verdict|Compliance Hook Verdict|Verdict)[:：][[:space:]]*(PASS|FAIL|pass|fail|通过|失败)'; then
  HAS_COMPLIANCE_HOOK_VERDICT=true
fi

HAS_COMPLIANCE_RECEIPT=false
if [ "$HAS_COMPLIANCE_SKILL" = true ] && [ "$HAS_COMPLIANCE_HOOK_COMMAND" = true ] && [ "$HAS_COMPLIANCE_HOOK_EXIT" = true ] && [ "$HAS_COMPLIANCE_HOOK_VERDICT" = true ]; then
  HAS_COMPLIANCE_RECEIPT=true
fi

HAS_STAGE2_CONTEXT_SECTION=false
if echo "$RESPONSE" | grep -Fq 'Stage 2 推荐门禁上下文摘要'; then
  HAS_STAGE2_CONTEXT_SECTION=true
fi

HAS_STAGE2_RECOMMENDATION_SECTION=false
if echo "$RESPONSE" | grep -Fq 'Stage 2 推荐门禁清单'; then
  HAS_STAGE2_RECOMMENDATION_SECTION=true
fi

STAGE2_CONTEXT_BLOCK="$(printf '%s\n' "$RESPONSE" | awk '
  BEGIN { capture = 0 }
  /Stage 2 推荐门禁上下文摘要/ { capture = 1; next }
  /Stage 2 推荐门禁清单/ { capture = 0 }
  capture { print }
')"

STAGE2_RECOMMENDATION_BLOCK="$(printf '%s\n' "$RESPONSE" | awk '
  BEGIN { capture = 0 }
  /Stage 2 推荐门禁清单/ { capture = 1; next }
  /^Compliance Skill:/ { capture = 0 }
  /^状态[:：]/ { capture = 0 }
  /^### / { capture = 0 }
  capture { print }
')"

HAS_STAGE2_MINIMUM_STRUCTURE=false
if printf '%s\n' "$STAGE2_CONTEXT_BLOCK" | grep -Fq -- '- task_goal:' \
  && printf '%s\n' "$STAGE2_CONTEXT_BLOCK" | grep -Fq -- '- change_objects:' \
  && printf '%s\n' "$STAGE2_CONTEXT_BLOCK" | grep -Fq -- '- change_summary:' \
  && printf '%s\n' "$STAGE2_CONTEXT_BLOCK" | grep -Fq -- '- executed_commands:' \
  && printf '%s\n' "$STAGE2_CONTEXT_BLOCK" | grep -Fq -- '- existing_evidence:' \
  && printf '%s\n' "$STAGE2_CONTEXT_BLOCK" | grep -Fq -- '- risk_points:' \
  && printf '%s\n' "$STAGE2_RECOMMENDATION_BLOCK" | grep -Fq -- '- change_type:' \
  && printf '%s\n' "$STAGE2_RECOMMENDATION_BLOCK" | grep -Fq -- '- change_summary:' \
  && printf '%s\n' "$STAGE2_RECOMMENDATION_BLOCK" | grep -Fq -- '- impact_scope:' \
  && printf '%s\n' "$STAGE2_RECOMMENDATION_BLOCK" | grep -Fq -- '- recommended_checks:' \
  && printf '%s\n' "$STAGE2_RECOMMENDATION_BLOCK" | grep -Fq -- '- reason:' \
  && printf '%s\n' "$STAGE2_RECOMMENDATION_BLOCK" | grep -Fq -- '- severity:' \
  && printf '%s\n' "$STAGE2_RECOMMENDATION_BLOCK" | grep -Fq -- '- requires_user_confirmation:'; then
  HAS_STAGE2_MINIMUM_STRUCTURE=true
fi

CLAIMS_RESULT=false
if [ "$CLAIMS_COMPLETION" = true ] || [ "$CLAIMS_MODIFICATION" = true ] || [ "$HAS_STANDARD_STATUS_DECLARATION" = true ]; then
  CLAIMS_RESULT=true
fi

if [ "$VERBOSE" = true ]; then
  echo "[compliance-hook] claims_completion=$CLAIMS_COMPLETION claims_modification=$CLAIMS_MODIFICATION has_status=$HAS_STANDARD_STATUS_DECLARATION unverified_status=$IS_EXPLICIT_UNVERIFIED has_evidence=$HAS_VERIFICATION_EVIDENCE status_payload_result=$STATUS_PAYLOAD_HAS_RESULT missing_verification_words=$MISSING_VERIFICATION has_env_sensitive_change=$HAS_ENVIRONMENT_SENSITIVE_CHANGE has_real_environment_evidence=$HAS_REAL_ENVIRONMENT_EVIDENCE has_compliance_skill=$HAS_COMPLIANCE_SKILL has_hook_command=$HAS_COMPLIANCE_HOOK_COMMAND has_hook_exit=$HAS_COMPLIANCE_HOOK_EXIT has_hook_verdict=$HAS_COMPLIANCE_HOOK_VERDICT has_compliance_receipt=$HAS_COMPLIANCE_RECEIPT has_stage2_context=$HAS_STAGE2_CONTEXT_SECTION has_stage2_recommendation=$HAS_STAGE2_RECOMMENDATION_SECTION has_stage2_structure=$HAS_STAGE2_MINIMUM_STRUCTURE" >&2
fi

if [ "$REQUIRE_STANDARD_STATUS" = true ]; then
  if [ "$CLAIMS_RESULT" = true ] && [ "$HAS_STANDARD_STATUS_DECLARATION" = false ]; then
    echo "⚠️  Missing standardized final status line."
    echo "Expected last line format:"
    echo "  状态：完成（已验证：<command/results>）"
    echo "  状态：修改（已验证：<command/results>）"
    echo "  状态：修改（未验证：<reason>）"
    exit 1
  fi
fi

if [ "$CLAIMS_RESULT" = true ] && [ "$REQUIRE_COMPLIANCE_RECEIPT" = true ] && [ "$HAS_COMPLIANCE_RECEIPT" = false ]; then
  echo "⚠️  Missing compliance-reviewer receipt block."
  echo "Required fields in report body:"
  echo "  Compliance Skill: \$compliance-reviewer"
  echo "  Hook Command: ...pre-completion-check.sh"
  echo "  Hook Exit: <code>"
  echo "  Hook Verdict: PASS|FAIL"
  exit 1
fi

if [ "$CLAIMS_RESULT" = true ] && [ "$REQUIRE_STAGE2" = true ]; then
  if [ "$HAS_STAGE2_CONTEXT_SECTION" = false ] || [ "$HAS_STAGE2_RECOMMENDATION_SECTION" = false ]; then
    echo "⚠️  Missing Stage 2 recommendation sections."
    echo "Required sections when COMPLIANCE_REVIEW_REQUIRE_STAGE2=true:"
    echo "  Stage 2 推荐门禁上下文摘要"
    echo "  Stage 2 推荐门禁清单"
    exit 1
  fi

  if [ "$HAS_STAGE2_MINIMUM_STRUCTURE" = false ]; then
    echo "⚠️  Incomplete Stage 2 recommendation structure."
    echo "Required fields include:"
    echo "  - task_goal:"
    echo "  - change_objects:"
    echo "  - change_summary:"
    echo "  - executed_commands:"
    echo "  - existing_evidence:"
    echo "  - risk_points:"
    echo "  - change_type:"
    echo "  - change_summary:"
    echo "  - impact_scope:"
    echo "  - recommended_checks:"
    echo "  - reason:"
    echo "  - severity:"
    echo "  - requires_user_confirmation:"
    exit 1
  fi
fi

if [ "$CLAIMS_RESULT" = true ]; then
  # If explicitly marked as unverified, allow without positive evidence.
  if [ "$IS_EXPLICIT_UNVERIFIED" = false ]; then
    if [ -z "$STATUS_PAYLOAD_CLEAN" ]; then
      echo "⚠️  Completion/modification claim has empty verification payload."
      echo "Provide concrete verification details in status line or body."
      exit 1
    fi

    if { [ "$HAS_VERIFICATION_EVIDENCE" = false ] && [ "$STATUS_PAYLOAD_HAS_RESULT" = false ]; } || [ "$MISSING_VERIFICATION" = true ]; then
      echo "⚠️  Completion/modification claim without sufficient verification evidence."
      echo "Provide concrete verification or explicitly disclose unverified status."
      exit 1
    fi

    if [ "$HAS_ENVIRONMENT_SENSITIVE_CHANGE" = true ] && [ "$HAS_REAL_ENVIRONMENT_EVIDENCE" = false ]; then
      echo "⚠️  Environment-sensitive change is missing real-environment verification evidence."
      echo "Provide explicit real-environment verification evidence or use an unverified status."
      exit 1
    fi

    if ! printf '%s\n' "$RESPONSE" | COMPLIANCE_REVIEW_VERBOSE="$VERBOSE" python3 "$EXECUTABLE_RECHECK_SCRIPT"; then
      exit 1
    fi
  fi
fi

exit 0
