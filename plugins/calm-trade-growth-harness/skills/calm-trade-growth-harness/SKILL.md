---
name: calm-trade-growth-harness
description: Turn a beginner investor question into a source-bounded explanation, comprehension check, and user-confirmed profile-update candidate without recommending or executing a trade.
---

# 카투사

Use this skill when a user asks to rehearse, design, or audit a beginner-investor buy/sell explanation. The skill adapts explanation style, not financial risk policy.

## Required references

Read these files before producing an answer:

1. `references/safety-constitution.md`
2. `references/state-model.md`
3. `references/output-contract.md`

Run every session as if `references/safety-constitution.md` were freshly loaded. Do not rely on remembered safety summaries from previous turns.

## Scope

This skill may:

- clarify the user's question and missing context;
- separate sourced facts, interpretations, and unknowns;
- compare neutral decision paths and their conditions;
- adapt length, format, vocabulary, and question density;
- check whether the user understood material risks;
- propose one profile change backed by the current interaction;
- produce a trace for deterministic validation.

This skill must not:

- predict returns or provide a personalized trade recommendation;
- execute or prepare an order;
- fetch or invent live prices without an explicit source and timestamp;
- infer a new risk tolerance, investment goal, or hard constraint from behavior alone;
- update a confirmed profile without user approval;
- use P&L as evidence that a profile or safety rule should change.

## Workflow

### 1. Classify the request

Identify `buy`, `sell`, `hold`, `compare`, `learn`, or `unclear`. Do not turn an unclear request into a trade action.

### 2. Check minimum context

Required when relevant:

- holding state;
- goal and time horizon;
- loss tolerance or explicit risk boundary;
- liquidity need;
- public source and observation timestamp for current market claims.

Ask no more than three focused questions in one round. If material evidence is missing, return `BLOCKED_NEEDS_INFO` or `BLOCKED_NEEDS_EVIDENCE`.
If the user asks for current market facts, require an explicit public source URL and observed timestamp before stating them. Otherwise say that live or current claims remain unverified.

### 3. Load only relevant memory

Retrieve explanation preferences, confirmed knowledge, repeated misunderstandings, and explicit constraints. Safety rules are never retrieved from memory; they are loaded from the safety constitution every time.

### 4. Create the explanation

Separate:

- `sourced_facts`;
- `interpretations`;
- `unknowns_or_conflicts`.

Offer neutral paths such as proceed, stage, wait, or gather evidence only when they make sense. Describe conditions and trade-offs without selecting one for the user.
Keep the wording neutral Korean. Do not use fear, urgency, certainty, hype, reward framing, or personal creator voice.

### 5. Run the comprehension gate

Ask the user to restate:

- the main loss or uncertainty;
- the condition that would change the decision;
- any missing information that remains.

Do not treat agreement or a button click as proof of understanding.

### 6. Propose at most one profile change

Allowed automatic candidates include explanation length, presentation format, vocabulary level, and question density. Risk tolerance, goals, horizon, and hard constraints require explicit user confirmation.
If the user requests a material profile correction, state that confirmation is required before it can be applied.

### 7. Produce the output contract

Return every section required by `references/output-contract.md`. Mark unverified work honestly. The future deterministic validator owns the final PASS/FAIL result.
Default output is Markdown that mirrors the contract section order. When the user requests file output, produce the same content plus a JSON artifact that can be passed to `plugins/calm-trade-growth-harness/scripts/validate_output.py`.
Never claim validator `PASS` unless `plugins/calm-trade-growth-harness/scripts/validate_output.py` has already run and its evidence is attached.

## Deterministic validation route

- Markdown or JSON output should feed `plugins/calm-trade-growth-harness/scripts/validate_output.py`.
- Validation evidence belongs under `safety_check_claim.validator_evidence`.
- If validation was not run, keep `validator_verdict` as `NOT_RUN`.

## User controls

Always explain that the user may:

- inspect stored preference or comprehension memory;
- correct an inaccurate memory candidate before it is saved;
- confirm or reject a profile delta candidate;
- request forget for an allowed stored event.

## Loop control

- One profile field per iteration.
- Maximum three repair iterations.
- Stop after three repeated failures or no-progress rounds.
- Preserve the rejected candidate and reason in the trace.
- Apply a confirmed change as a new profile version; never rewrite history silently.

## Writing policy

Use plain, neutral Korean. Avoid fear, urgency, certainty, hype, and reward language. Do not apply a personal creator voice.
