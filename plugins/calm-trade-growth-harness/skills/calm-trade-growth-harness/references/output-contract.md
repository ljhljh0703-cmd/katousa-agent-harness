# Output Contract

Every run returns these sections in order.

1. `status`
   - `READY_FOR_USER_DECISION`
   - `BLOCKED_NEEDS_INFO`
   - `BLOCKED_NEEDS_EVIDENCE`
   - `BLOCKED_HUMAN_REVIEW`
2. `request_summary`
3. `missing_information`
4. `sourced_facts`
   - claim
   - source URL
   - observed_at
5. `interpretations`
6. `unknowns_or_conflicts`
7. `decision_paths`
   - path name
   - conditions
   - trade-offs
   - what would change the path
8. `personalized_explanation`
9. `comprehension_check`
10. `memory_candidate`
11. `profile_delta_candidate`
12. `safety_check_claim`
   - This is a claim until the deterministic validator runs.
13. `trace_id`

The output must include this boundary in natural language:

> 이 결과는 판단을 돕는 설명 자료이며 종목 추천이나 주문 실행이 아닙니다.

Do not claim `PASS` unless the validator output is attached to the run evidence.
