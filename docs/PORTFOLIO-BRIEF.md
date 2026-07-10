# Portfolio Brief — Two Financial Agent Harnesses

Status: evidence-backed draft updated on 2026-07-10. Claims below are limited to verified implementation and dry-run evidence.

## Recommended title

**금융 AI를 두 번 설계하며 배운 것 — 모델보다 하네스, 자동화보다 통제 가능한 성장**

English working title:

**Two Financial Agent Harnesses: Constraining Action, Governing Adaptation**

## 30-second summary

현수봇은 AI가 실제 행동을 제안하는 고위험 시스템에서 판단과 실행을 분리하고, 모든 진입을 결정론적 리스크 게이트와 dry-run 평가로 제한한 프로젝트다. 카투사는 같은 원칙을 금융 소비자 설명에 옮긴다. 사용자의 선호와 이해 수준에 따라 설명은 달라져도 출처, 비권유, 비실행, 확인 없는 material 변경 금지는 고정한다. 두 프로젝트는 범용 에이전트 하나를 포장한 사례가 아니다. AI 에이전트는 불확실한 해석, 하네스는 위반 불가능한 경계, 루프는 관찰이 다음 상태 후보가 되는 절차를 맡는다. 도메인별 실패 조건에 따라 이 세 역할을 다시 설계한 연속 사례다.

## Portfolio thesis

> AI 에이전트의 품질은 모델 이름보다 모델이 바꿀 수 있는 것, 바꿀 수 없는 것, 실패했을 때 멈추는 조건을 어떻게 설계했는지에서 갈린다.

Public-facing pair thesis:

> 돈을 움직이는 AI는 행동을 통제하고, 사람에 맞춰 변하는 AI는 적응을 통제했습니다.

- 현수봇: **퀀트형 자동매매 에이전트를 통제하는 행동 하네스**
- 카투사: **초보 투자자에게 맞춰 성장하는 설명 에이전트를 통제하는 헤르메스형 하네스**

`헤르메스형`은 이 포트폴리오에서 `관찰 → 한 필드 변경 후보 → 검증 → 사용자 승인 → 버전 적용`을 가리키는 설명 용어다. 자동 자기개조나 온라인 학습을 주장하지 않는다. 일반 독자에게는 “초보 투자자용 적응형 설명 하네스”를 먼저 쓴다.

## Role separation — 세 역할을 한 덩어리로 부르지 않기

| Role | Hyunsoo Bot | 카투사 | Evidence boundary |
|---|---|---|---|
| AI 에이전트 | 시장 해석과 진입 후보 신호를 만든다. | 질문 분류, 출처가 묶인 설명, 중립적 선택 경로, 이해 확인 질문을 만든다. | 생성 품질이나 수익·이해 향상을 증명했다는 뜻이 아니다. |
| 하네스 엔지니어링 | RiskManager, kill switch, 한도, TP/SL, dry-run gate가 행동 가능 범위를 제한한다. | schema, output validator, one-change rule, 확인 필수 필드, audit/forget, package verifier가 출력과 상태 전이를 제한한다. | 결정론 gate 통과는 production readiness나 법률 적합성 인증이 아니다. |
| 루프 엔지니어링 | decision journal에서 dry-run 프로세스를 검토하고 원칙 변경안을 staged proposal로 남긴 뒤 사람의 승인을 요구한다. | 대화 사건 → 이해 확인 → 한 필드 후보 → 사용자 확인 → versioned apply → replay/circuit breaker로 이어진다. | 자동 학습이나 사용자 성과 개선이 아니라 제안·검증·승인 절차를 구현한 것이다. |

직접 내린 설계 결정:

- 두 프로젝트에서 모델 호출 수나 프롬프트 길이가 아니라 변경 권한과 stop condition을 포트폴리오의 중심 증거로 삼았다.
- 현수봇의 loop 증거는 dry-run trace와 staged proposal까지만 인정하고 실거래 outcome으로 확대하지 않았다.
- 카투사의 이해 실패는 설명 형식 후보의 근거로만 쓰고 위험성향이나 안전 규칙 변경 근거로 쓰지 않았다.

## Cross-case structure

| Question | Hyunsoo Bot | 카투사 |
|---|---|---|
| Domain failure | Unchecked action can create financial loss. | Personalization can amplify bias, certainty, or financial pressure. |
| Fuzzy responsibility | Market interpretation and candidate signal. | Intent interpretation and explanation composition. |
| Deterministic spine | RiskManager, kill switch, limits, TP/SL, dry-run. | Source rules, no recommendation/execution, profile transition rules, loop caps. |
| Memory | Decision journal and staged principle improvement. | Append-only preference and comprehension events. |
| Loop | decision -> dry-run trace -> process review -> staged principle proposal -> human approval | conversation -> comprehension -> profile candidate -> replay -> approval |
| Human authority | live transition and rule adoption require gates. | material profile changes and final decision remain with the user. |
| Evidence | dry-run process metrics and trace. | safety replay, profile mutation tests, package and trace reports. |
| Forbidden claim | real-trading profitability. | investment returns, advice accuracy, or KakaoPay Securities integration. |

## Claim-to-evidence review

- Verified: 현수봇은 AI 판단과 결정론적 리스크 제어를 나누며, 고정 fixture dry-run eval을 제공한다. 근거는 공개 commit 5ae142ff5837cf23f26547536f32dbc5fdb0bd32의 README.md, brain/risk_manager.py, brain/eval_harness.py다.
- Verified: 현수봇의 reflection은 원칙 변경안을 staging하며 risk_config를 자동 변경하지 않는다. 근거는 같은 commit의 brain/reflector.py, brain/principle_kb.py, brain/test_principles.py다.
- Verified: 카투사의 agent/harness/loop는 각각 SKILL.md, contracts.py 및 validate_output.py, state.py 및 replay.py로 분리되어 있다. 29개 unit test, 30회 replay, CLI state/forget smoke로 경계를 재현했다.
- Verified: 개인정보를 제거하고 실제 사건 순서만 보존한 재구성 개발 맥락 1개로 최종 제출 ZIP을 빌드하고 검증했다. 이 기록은 원문 대화나 직접 인용이 아니다.
- Blocked: 카투사가 실제 사용자의 이해를 개선했다는 주장과 개별 AI 제안 거절의 원문 대조는 아직 증거가 없다.
- Prohibited: 두 프로젝트의 투자 성과, 카카오페이증권 공식 연동, production readiness, 법률·컴플라이언스 적합성을 주장하지 않는다.

## Case-study order

### 1. Wound

The same model can produce fluent output in both systems. Fluency is not the hard problem. The hard problem is that an agent may act beyond its evidence or adapt in a way the user did not authorize.

### 2. First decision — separate fuzzy and deterministic work

Explain why the author separated model judgment from risk and state transitions instead of asking one agent to do everything.

### 3. Hyunsoo Bot — constrain action

Evidence-backed points only:

- Python Brain and Rust Spine separation;
- deterministic RiskManager and dry-run default;
- process metrics and reproducible eval trace;
- staged principle proposals instead of silent prompt mutation.

Boundary:

- no real-trading performance claim;
- describe reflection and principle loops only to the extent implemented and verified in the public repo.

### 4. 카투사 — govern adaptation

Show how the same model+harness principle changes in a user-facing financial explanation domain:

- immutable safety constitution;
- mutable explanation style;
- confirmed material profile fields;
- ephemeral emotional context;
- append-only memory and privacy-aware forget path;
- one-change loop, replay evaluation, circuit breaker, and rollback.

Direct author decision:
The author did not let comprehension failure or P&L push a silent profile rewrite. 카투사는 한 번에 하나의 변경 후보만 기록하고, 확인 근거가 없는 material field를 차단하며, 반복된 repair 실패 뒤에는 새 규칙을 즉흥적으로 만들지 않고 멈춘다.

### 5. What changed in the author's thinking

The design moved from controlling an agent's external action to controlling an agent's internal adaptation. A kill switch is enough for an order path. It is not enough when the system can gradually shape how a user understands risk. The second system therefore treats memory and profile mutation as first-class safety surfaces.

### 6. Proof

Use a compact evidence board:

- public commit SHA;
- plugin manifest validation;
- unit-test count and exit status;
- replay matrix by explanation profile;
- sample blocked trace;
- profile delta before/after with confirmation;
- package verification and SHA-256;
- claim ledger.

Current verified board:

- Hyunsoo Bot reference commit: `5ae142ff5837cf23f26547536f32dbc5fdb0bd32`
- 카투사 plugin validator: exit `0`
- 카투사 skill validator: exit `0`, `Skill is valid!`
- 카투사 unit tests: `29` passed
- 카투사 replay: `30` runs, `all_invariants_stable: true`
- 카투사 package verification: `dist/submission.zip`, rebuilt from one `PRIVACY-SAFE RECONSTRUCTED CONTEXT` log
- 카투사 package SHA-256: `797d4e2a1cbc26e2d6b8c3245457729fcf95330bb33c5f343a992541c6f9e8a1` (`27724` bytes)
- Claim ledger: `docs/EVIDENCE-MAP.md`

### 7. Honest limitations

- hackathon prototype, not production financial software;
- no live market data or brokerage connection in MVP;
- no claim that comprehension improvement changes financial outcomes;
- compliance interpretation requires domain review;
- model-generated explanations remain fallible even when the harness passes.
- final packaging proves byte-preserving inclusion of the reconstructed artifact and package safety checks; it does not convert that artifact into a raw transcript or direct quotation.

## Resume bullets after implementation

Do not publish until the evidence map marks the relevant claim `verified`.

- Designed a Codex plugin that separates adaptive financial explanation from immutable safety and profile-transition rules, verified by the local plugin validator and replay gate.
- Implemented an append-only user-memory and replay loop that changes one explanation preference at a time, requires confirmation for material financial context, and preserves forget receipts without deleted payload.
- Extended the model+harness pattern from a dry-run trading agent to a consumer-facing decision-support agent, with proof anchored in process evidence, not P&L claims.

## Interview answer frame

1. Start with the failure condition, not the tool name.
2. Explain the decision the author made.
3. Show which responsibility belongs to the model and which belongs to code.
4. Show one rejected alternative.
5. Finish with proof and remaining limitation.

Rejected alternatives worth preserving:

- live price or brokerage integration for the MVP;
- P&L-driven persona changes;
- silent risk-profile inference;
- autonomous self-modification;
- MCP or multi-agent complexity without a verified need;
- applying a personal voice layer to portfolio copy.

## Public writing policy

- Use fact lock and structural editing first.
- Apply a surgical Korean humanization pass to remove translation-like and generic AI prose.
- Use product-writing principles only for UI and demo copy.
- Do not apply `juhyeong-voice`.
- Do not smooth over failure, `not run`, or implementation gaps.

## Canonical public artifacts

- Publish-ready case study: `docs/PORTFOLIO-CASE-STUDY.md`
- Resume/interview copy: `docs/PORTFOLIO-COPY-KIT.md`
- Public-safe replay snapshot: `docs/portfolio-evidence.json`
- Publication and user-study plan: `docs/PORTFOLIO-PUBLISH-PLAN.md`

## CTA

Primary CTA after implementation:

- Run the fixed replay demo.
- Inspect a blocked trace.
- Compare the same safety explanation across three user presentation profiles.
- Open the public code and evidence map.
