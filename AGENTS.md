# AGENTS.md

This repository contains a Codex plugin, a hackathon submission packager, and public portfolio evidence.

## Authority order

1. `_dev/AGENTS.md` and the newest unreturned `_dev/DISPATCH-*.md`, when present locally.
2. `docs/IMPLEMENTATION-SPEC.md`.
3. `plugins/calm-trade-growth-harness/skills/calm-trade-growth-harness/SKILL.md`.
4. Tests and fixtures.
5. Public README and portfolio copy.

If these disagree, stop and report the mismatch. Do not silently blend contracts.

## Non-negotiable boundaries

- This is decision-support explanation tooling, not investment advice or order execution.
- Do not add live brokerage, exchange, account, portfolio, or market-data credentials.
- Do not infer or mutate risk tolerance, goals, or hard constraints without explicit user confirmation.
- Do not let P&L outcomes modify the safety constitution or user profile.
- Do not claim a production integration, KakaoPay Securities endorsement, hackathon result, or investment performance.
- Keep `_dev/`, `logs/`, `dist/`, `.calm-trade/`, and secrets out of Git.
- Never use `git add -A` or `git add .`; stage named public files only when the user asks.

## Development protocol

1. Contract and fixtures before runtime code.
2. Keep fuzzy language generation separate from deterministic validation and state transitions.
3. Change one profile field per loop iteration.
4. Preserve append-only event provenance. A forget request deletes payload and records only a non-sensitive deletion receipt.
5. Run the declared tests and package verification before claiming completion.
6. Report `PASS`, `FAIL`, `BLOCKED`, and `NOT IMPLEMENTED` precisely.

## Public writing

- Portfolio prose: fact lock, structural edit, `humanize-korean`-style surgical de-AI pass.
- Product/UI copy: the same fact lock and de-AI pass, followed by `toss-ux-writing` principles.
- Do not apply `juhyeong-voice` to this repository.
- Do not edit technical names, source URLs, dates, metrics, commit SHAs, or claim direction during polishing.

## Verification

The implementation dispatch defines exact commands. At minimum, verify:

- plugin manifest validation;
- unit tests and replay eval;
- stable safety results across different explanation profiles;
- no silent profile mutation;
- package layout and size;
- secret scan and `_dev`/`dist`/private-log exclusion;
- public claim-to-evidence mapping.
