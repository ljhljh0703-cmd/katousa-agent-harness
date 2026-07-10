# Writing Policy

## Purpose

Keep public claims accurate while removing translation-like and generic AI prose. This repository does not use a personal voice layer.

## Portfolio and README prose

Apply this order:

1. Fact lock: names, numbers, dates, URLs, commit SHAs, implementation status, claim direction.
2. Structure: problem, decision, implementation, proof, boundary.
3. Humanize: edit only spans that show translation-like phrasing, generic hype, repetitive structure, or unnecessary abstraction.
4. Fidelity recheck: no missing facts, invented facts, polarity changes, or causal changes.

Hard boundaries:

- Do not apply `juhyeong-voice`.
- Do not add humor, personal catchphrases, or a creator persona.
- Do not rewrite more than necessary. A large rewrite requires a second fact-lock pass.
- Keep `planned`, `implemented`, `verified`, `not run`, and `blocked` distinct.

## Product and UI copy

After the fact-lock and humanize pass, apply these rules:

- Use one clear message per screen.
- Prefer active voice and familiar words.
- Suggest rather than pressure.
- Do not use fear, urgency, certainty, or reward language to push a financial action.
- Explain acronyms on first use.
- Keep errors actionable: say what information is missing and how to continue.

Examples:

- Avoid: `지금 확인하지 않으면 기회를 놓칠 수 있어요.`
- Use: `판단에 필요한 정보가 아직 부족해요. 투자 기간과 손실 감수 범위를 먼저 확인해 주세요.`
- Avoid: `안전한 선택입니다.`
- Use: `이 설명은 손실 가능성을 포함한 비교 자료예요. 최종 결정은 사용자가 내려요.`

## Review checklist

- [ ] Technical names and source anchors unchanged
- [ ] Numbers, dates, and SHAs unchanged
- [ ] No invented user outcome or KPI
- [ ] No production or endorsement implication
- [ ] No investment pressure or guaranteed-return language
- [ ] No `juhyeong-voice` layer
