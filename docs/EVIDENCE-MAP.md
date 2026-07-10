# Evidence Map

Status values:

- `verified`: reproduced or directly inspected.
- `implemented_unverified`: code exists but the declared gate has not run.
- `planned`: specified but not implemented.
- `prohibited`: must not be claimed.

| ID | Public claim | Status | Evidence |
|---|---|---|---|
| HYS-01 | Hyunsoo Bot separates AI judgment from deterministic risk controls. | verified | Public repo README at commit `5ae142ff5837cf23f26547536f32dbc5fdb0bd32` |
| HYS-02 | Hyunsoo Bot includes a dry-run eval harness and process metrics. | verified | `make eval` contract in public repo; local reproduction used `PYTHONPATH=brain python3 brain/eval_harness.py` at the same commit |
| HYS-03 | Hyunsoo Bot dry-run gates reported PASS for the current fixed fixture. | verified | `eval_report.md`, `metrics.json`, and reproduced command output; label as dry-run only |
| HYS-04 | Hyunsoo Bot has proven real-trading profitability. | prohibited | No accepted evidence; dry-run metrics are not P&L |
| HYS-05 | Hyunsoo Bot records dry-run decisions, stages principle proposals, and keeps risk configuration outside automatic reflection writes. | verified | Fresh clone at commit `5ae142ff5837cf23f26547536f32dbc5fdb0bd32`; inspected `brain/decision_journal.py`, `brain/reflector.py`, `brain/principle_kb.py`, and `brain/test_principles.py` |
| CT-01 | 카투사는 valid plugin manifest와 skill scaffold를 갖는다. | verified | Command: `python3 "$CODEX_HOME/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/calm-trade-growth-harness`; CWD: repo root; Exit: `0`; Result: `Plugin validation passed`; Evidence: `plugins/calm-trade-growth-harness/.codex-plugin/plugin.json`, `plugins/calm-trade-growth-harness/README.md`, `plugins/calm-trade-growth-harness/skills/calm-trade-growth-harness/SKILL.md` |
| CT-02 | 카투사는 checklist, numbers, example profile 전반에서 안전 불변식을 유지하며 설명 방식을 조절한다. | verified | Commands: `python3 -m unittest discover -s tests -v`, `python3 scripts/run_replay_eval.py --out dist`; CWD: repo root; Exit: `0`, `0`; Results: `29` unit tests passed, replay `30` runs with `all_invariants_stable: true`; Evidence: `tests/test_replay.py`, `dist/replay-report.md`, `dist/replay-metrics.json`, `dist/replay-trace.jsonl` |
| CT-03 | 카투사는 확인 없는 material profile 변경을 막고 privacy-aware forget receipt를 보존한다. | verified | Command: `python3 -m unittest discover -s tests -v`; CWD: repo root; Exit: `0`; Evidence: `tests/test_state.py`; Verified cases: no silent update, confirmation required for material fields, P&L mutation rejection, forget payload removal |
| CT-04 | 카투사는 `TEST_ONLY` fixture log로 해커톤 ZIP layout을 만들고 검증할 수 있다. | verified | Commands: `python3 scripts/package_submission.py --logs fixtures/test-logs --out dist/test-submission.zip --test-only`, `python3 scripts/verify_submission.py dist/test-submission.zip --allow-test-only`; CWD: repo root; Exit: `0`, `0`; Evidence: `dist/test-submission.zip`, `dist/SHA256SUMS.txt`, `dist/package-report.md`, `tests/test_packaging.py` |
| CT-05 | 카투사가 투자자의 성과나 수익률을 개선한다. | prohibited | Not measured and outside scope |
| CT-06 | 카투사는 카카오페이증권의 제품이거나 공식 연동이다. | prohibited | Independent hackathon prototype only |
| CT-07 | 카투사는 개인정보를 제거한 재구성 개발 맥락 1개로 최종 패키지를 만들고 검증한다. | verified | Commands: `python3 scripts/package_submission.py --logs logs/privacy-safe --out dist/submission.zip`, `python3 scripts/verify_submission.py dist/submission.zip`; CWD: repo root; Exit: `0`, `0`; Result: `FINAL`, `1` reconstructed context log, `27724` bytes, privacy-pattern scan `0`, SHA-256 `797d4e2a1cbc26e2d6b8c3245457729fcf95330bb33c5f343a992541c6f9e8a1`. The included context is not a raw transcript or direct quotation. |
| CT-08 | 카투사는 AI-agent work, deterministic harness rule, user-confirmed state-change loop를 분리한다. | verified | Agent: `SKILL.md`; harness: `contracts.py`, `validate_output.py`; loop: `state.py`, `replay.py`; commands: 29 unit tests, 30 replay runs, plugin validator, skill validator, and state/forget CLI smoke |
| CT-09 | 카투사가 실제 사용자의 이해도를 개선했다. | prohibited | No user study or outcome measurement has been run |
| PORT-01 | 두 프로젝트는 도메인별 하네스 설계를 보여 준다. 현수봇은 행동을 제한하고, 카투사는 적응을 통제한다. | verified | Based on `HYS-01` to `HYS-03`, `HYS-05`, `CT-01` to `CT-04`, and `CT-08`; public framing captured in `docs/PORTFOLIO-BRIEF.md` |
| PORT-02 | AI agent, harness engineering, and loop engineering are distinct portfolio responsibilities in both projects. | verified | Role-to-file mapping in `docs/PORTFOLIO-BRIEF.md`; source claims are bounded by `HYS-01`, `HYS-02`, `HYS-05`, `CT-02`, `CT-03`, and `CT-08` |
| PORT-03 | 카투사의 공개용 정상·차단·확인 필요 증거 스냅샷은 고정 fixture replay에서 다시 만들 수 있다. | verified | Command: `python3 scripts/export_portfolio_evidence.py`; Evidence: `scripts/export_portfolio_evidence.py`, `tests/test_portfolio_evidence.py`, `docs/portfolio-evidence.json` |
| PORT-04 | “헤르메스형 하네스”는 통제된 사용자 적응 루프를 설명하는 포트폴리오 용어다. | verified | Loop mapping: `state.py`, `replay.py`, one-change rule, confirmation, versioned apply, circuit breaker. It is not a claim of autonomous self-modification or online learning. |

## Verification note

On 2026-07-10, `git ls-remote origin` returned `5ae142ff5837cf23f26547536f32dbc5fdb0bd32` for both `HEAD` and `refs/heads/main`. A fresh clone at that commit reproduced the harness with the available system Python using:

```text
PYTHONPATH=brain python3 brain/eval_harness.py
```

Reported results remain dry-run process metrics and must never be presented as investment performance.

The reproduced summary was: 3 simulated entries, 100.0% risk-rule compliance, 100.0% TP/SL attachment, kill-switch accuracy true, daily-loss-limit block true, deterministic true, and `ALL GATES PASS`. These are fixed-fixture dry-run process results, not trading performance.
