# Evidence Map

Status values:

- `verified`: reproduced or directly inspected.
- `implemented_unverified`: code exists but the declared check has not run.
- `planned`: specified but not implemented.
- `prohibited`: must not be claimed.

| ID | Public claim | Status | Evidence |
|---|---|---|---|
| CT-01 | 카투사는 valid plugin manifest와 skill scaffold를 갖는다. | verified | Command: `python3 "$CODEX_HOME/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/calm-trade-growth-harness`; Exit: `0`; Result: `Plugin validation passed` |
| CT-02 | 카투사는 checklist, numbers, example 형식에서도 같은 안전 판단을 유지한다. | verified | Commands: `python3 -m unittest discover -s tests -v`, `python3 scripts/run_replay_eval.py --out dist`; Results: `29` unit tests passed, replay `30` runs, invariant mismatches `0` |
| CT-03 | 카투사는 확인 없는 중요 프로필 변경을 막는다. | verified | `tests/test_state.py`: no silent update, confirmation required for material fields, P&L mutation rejection |
| CT-04 | 카투사는 저장된 사건의 원문을 삭제하고 내용 없는 삭제 영수증만 남길 수 있다. | verified | `tests/test_state.py`: forget payload removal, unique monotonic event IDs, deletion receipt |
| CT-05 | 출처와 확인 시각이 없는 현재 정보는 결론을 보류한다. | verified | `live_claim_without_source` fixture across three profiles; status `BLOCKED_NEEDS_EVIDENCE` |
| CT-06 | 핵심 출처가 충돌하면 사람의 검토 전까지 결론을 보류한다. | verified | `conflicting_sources` fixture across three profiles; status `BLOCKED_HUMAN_REVIEW` |
| CT-07 | 반복 실패는 세 번에서 중단한다. | verified | `tests/test_state.py`, `repeated_failure_circuit_breaker` fixture |
| CT-08 | 카투사는 AI 생성, 결정론적 안전 검사, 사용자 확인 기반 상태 변경을 분리한다. | verified | Agent: `SKILL.md`; validation: `contracts.py`, `validate_output.py`; state loop: `state.py`, `replay.py` |
| CT-09 | 공개용 정상·차단·확인 필요 증거는 고정 fixture에서 다시 만들 수 있다. | verified | `scripts/export_portfolio_evidence.py`, `tests/test_portfolio_evidence.py`, `docs/portfolio-evidence.json` |
| CT-10 | 카투사가 실제 사용자의 이해도를 개선했다. | prohibited | User study has not run |
| CT-11 | 카투사가 투자 성과나 수익률을 개선한다. | prohibited | Not measured and outside scope |
| CT-12 | 카투사는 카카오페이증권의 제품이거나 공식 연동이다. | prohibited | Independent prototype only |
| PORT-01 | 카투사는 초보 투자자에 맞춰 설명 방식만 조절하고 안전 기준은 고정하는 제품으로 설명할 수 있다. | verified | `CT-02`, `CT-03`, `CT-05`, `CT-06`, `CT-08` |
| PORT-02 | AI 에이전트, 하네스 엔지니어링, 루프 엔지니어링은 카투사 안에서 서로 다른 책임을 맡는다. | verified | Role-to-file mapping in `docs/PORTFOLIO-CASE-STUDY.md` and `CT-08` |

## Verification note

2026-07-10 기준 로컬과 새 공개 clone에서 다음을 재현했다.

- 단위 테스트 `29`개 통과
- 고정 사례 `10`개 × 설명 형식 `3`개 = `30`회 실행
- `15 PASS / 15 expected FAIL`
- 설명 형식별 안전 기준 불일치 `0`건
- 공개 증거 export 통과
- GitHub Actions Python 3.11·3.12 통과

이 결과는 프로세스와 안전 조건에 대한 검증이다. 투자 수익률, 실제 사용자 이해도, 법률·컴플라이언스 적합성을 증명하지 않는다.
