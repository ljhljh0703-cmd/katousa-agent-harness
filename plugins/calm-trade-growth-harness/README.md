# 카투사 플러그인

카카오 투자하는 사람의 질문을 기억해 설명은 점점 맞춰 가고, 안전 기준은 고정하는 투자 이해 파트너입니다.

> 수익률은 못 올려도, 이해도는 올려드립니다. 투자는 내가, 설명은 카투사가.

## Main files

- Skill entry: `skills/calm-trade-growth-harness/SKILL.md`
- Required references:
  - `skills/calm-trade-growth-harness/references/safety-constitution.md`
  - `skills/calm-trade-growth-harness/references/state-model.md`
  - `skills/calm-trade-growth-harness/references/output-contract.md`
- Deterministic scripts:
  - `scripts/init_state.py`
  - `scripts/record_event.py`
  - `scripts/propose_delta.py`
  - `scripts/apply_delta.py`
  - `scripts/forget.py`
  - `scripts/validate_output.py`

## Invocation examples

Use the skill for rehearsal, design, or audit prompts such as:

- `이 투자 질문을 설명 카드로 바꾸고 부족한 정보를 세 가지 안에서만 확인해 줘.`
- `같은 안전 기준을 유지하면서 숫자형 설명과 사례형 설명을 비교해 줘.`
- `이 응답 초안을 카투사 출력 계약에 맞춰 점검해 줘.`

## Validation flow

1. Produce Markdown in the section order required by `references/output-contract.md`.
2. If a file artifact is needed, also write a JSON payload that matches the same contract.
3. Run:

```bash
python3 plugins/calm-trade-growth-harness/scripts/validate_output.py path/to/output.json
```

4. Keep `safety_check_claim.validator_verdict` at `NOT_RUN` until that script succeeds.

## State transition flow

```bash
python3 plugins/calm-trade-growth-harness/scripts/init_state.py --state-dir .calm-trade
python3 plugins/calm-trade-growth-harness/scripts/record_event.py --state-dir .calm-trade --type preference --source-turn turn-1 --content "숫자형 설명 선호" --importance 2
python3 plugins/calm-trade-growth-harness/scripts/propose_delta.py --state-dir .calm-trade --field explanation_style.format --to '"numbers"' --basis-event-id evt_0001 --basis-summary "사용자가 숫자형 설명을 요청했다."
python3 plugins/calm-trade-growth-harness/scripts/apply_delta.py --state-dir .calm-trade --delta-id delta_0001 --source-turn turn-2 --confirm --confirmation-evidence "사용자 확인"
```

Forget flow:

```bash
python3 plugins/calm-trade-growth-harness/scripts/forget.py --state-dir .calm-trade --event-id evt_0001 --source-turn turn-3
```

## Plugin validation

Run the local plugin validator from the repository root:

```bash
python3 "$CODEX_HOME/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/calm-trade-growth-harness
```

The plugin is usable only when the validator passes and the skill keeps the deterministic validation step explicit.
