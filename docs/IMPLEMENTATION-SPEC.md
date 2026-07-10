# 카투사 — Implementation Specification

Version: 0.1.0
Status: `SPEC_READY`
Target: Codex plugin + hackathon submission + public portfolio evidence

## 1. Objective

Build a Codex plugin that turns a beginner-investor question into a source-bounded explanation, checks comprehension, and proposes a traceable user-profile change without recommending or executing a trade.

The system may learn how to explain. It must not learn to loosen safety rules or make the user more aggressive.

## 2. Primary user and beneficiary

Primary plugin user:

- AI service planner;
- product owner;
- UX writer or conversation designer;
- safety/compliance reviewer running a prototype review.

Beneficiary:

- a beginner investor who needs understandable decision support and a stable safety boundary.

## 3. Public problem basis

- KakaoPay Securities interview: beginner investors struggle with buy/sell decisions; the evaluation emphasizes the process that helps a user understand and proceed with confidence.
  - https://www.youtube.com/watch?v=aBuoojGjyf4
- Financial Services Commission guidance: customer information, material risk explanation, and confirmation of understanding matter in financial-product recommendation flows.
  - https://www.fsc.go.kr/po020201/75646
- Codex plugin structure:
  - https://learn.chatgpt.com/docs/build-plugins

This prototype is not a KakaoPay Securities product or legal/compliance implementation.

## 4. Design thesis

### 4.1 Model + harness

The language model owns interpretation and explanation. Deterministic code owns schema validation, safety invariants, profile transitions, loop caps, trace integrity, and packaging checks.

### 4.2 Adaptive surface, fixed spine

Adaptive surface:

- length;
- format;
- vocabulary;
- question density;
- examples;
- repeated misunderstanding support.

Fixed spine:

- no recommendation;
- no execution;
- source and timestamp requirements;
- uncertainty preservation;
- confirmation for material profile changes;
- audit and privacy rules.

### 4.3 Process metrics, not P&L

The evaluation measures rule compliance, source coverage, comprehension coverage, profile-change traceability, replay stability, and loop termination. It does not measure or claim investment performance.

## 5. Architecture

```text
User scenario + source bundle
        |
        v
Intent and context extraction            fuzzy
        |
        v
Relevant profile and memory retrieval    bounded state
        |
        v
Explanation composition                  fuzzy
        |
        v
Safety Spine validation                  deterministic
        |
        +---- blocked ----> reason + next information needed
        |
        v
Comprehension check                      user-facing gate
        |
        v
Profile delta candidate                  one field only
        |
        v
Replay evaluation                        deterministic fixtures
        |
        v
User confirmation -> versioned apply     controlled state transition
```

## 6. Components

### 6.1 Codex skill

Path:

`plugins/calm-trade-growth-harness/skills/calm-trade-growth-harness/SKILL.md`

Responsibilities:

- classify request;
- ask at most three missing-context questions;
- separate facts, interpretations, and unknowns;
- compose a neutral explanation;
- run a comprehension prompt;
- propose at most one profile change;
- produce the output contract.

### 6.2 Safety constitution

Path:

`skills/calm-trade-growth-harness/references/safety-constitution.md`

Loaded every run. Never retrieved from user memory or changed by the loop.

### 6.3 Workspace state

Runtime state lives under the user's working directory, not the installed plugin:

```text
.calm-trade/
├── profile.json
├── events.jsonl
├── profile-deltas.jsonl
├── traces/
└── state.json
```

The directory is private and excluded from Git by default.

### 6.4 Deterministic scripts

Implement with Python standard library unless a dependency is justified.

Required scripts:

- `init_state.py`: create a versioned default profile and empty event stores.
- `record_event.py`: append a validated event with provenance.
- `propose_delta.py`: create one profile-delta candidate.
- `apply_delta.py`: require confirmation evidence and increment the profile version.
- `forget.py`: delete target payload and append a non-sensitive deletion receipt.
- `validate_output.py`: validate output schema and safety invariants.
- `run_replay_eval.py`: run fixed cases across multiple explanation profiles.
- `package_submission.py`: build the required ZIP without editing raw logs.
- `verify_submission.py`: verify ZIP layout, size, manifest, excluded paths, and secret-scan result.

Do not create an MCP server for the MVP. Add one only if a tested live data source becomes necessary and its licensing, freshness, authentication, and safety boundaries are explicit.

## 7. Data contracts

### 7.1 Profile

Required fields:

```json
{
  "schema_version": "1.0",
  "profile_version": 1,
  "explanation_style": {
    "length": "short|balanced|detailed",
    "format": "numbers|example|checklist|dialogue",
    "vocabulary": "beginner|intermediate",
    "question_density": "low|medium|high"
  },
  "confirmed_decision_context": {
    "goal": null,
    "time_horizon": null,
    "loss_tolerance": null,
    "liquidity_need": null,
    "hard_constraints": []
  },
  "updated_at": "ISO-8601"
}
```

Fields under `confirmed_decision_context` change only with explicit confirmation.

### 7.2 Event

Events include ID, timestamp, type, source turn, minimal content, importance, profile version, and confirmation state. Reject secret-like or unnecessary financial payloads.

### 7.3 Output

The skill output follows `references/output-contract.md`. The implementation should also support JSON output for validation and a Markdown rendering for reviewers.

### 7.4 Trace

Each run records:

- input fixture or input hash;
- loaded profile version;
- loaded event IDs;
- source ledger;
- generated output path;
- validator result;
- proposed delta;
- confirmation state;
- stop reason;
- iteration and cost counters.

## 8. Loop specification

Cadence:

- event-driven after a completed explanation and comprehension check;
- no background autonomous writes in the hackathon MVP.

One-change rule:

- one profile field per candidate and per iteration.

Stable checks:

- output schema;
- safety invariants;
- fixed replay fixtures;
- same validator verdict for the same structured output;
- safety-equivalence across explanation profiles.

State file:

- `.calm-trade/state.json` stores active run, profile version, iteration count, last error signature, and rollback pointer.

Stop rules:

- success after validator PASS and user confirmation where required;
- block on missing evidence or material source conflict;
- maximum three repair iterations;
- hard stop after the same error signature occurs three times;
- hard stop when the proposed change touches an immutable or confirmation-required field without evidence.

Risk colors:

- green: read-only explanation and low-risk style candidate;
- yellow: profile change awaiting user confirmation;
- red: order execution, live account access, safety-rule mutation, or unapproved material profile change. Red actions are prohibited.

## 9. Test plan

### 9.1 Unit tests

- profile schema accepts a valid default and rejects unknown immutable mutations;
- event store appends and preserves provenance;
- one-change rule rejects multi-field deltas;
- apply requires confirmation for material fields;
- forget removes payload and leaves no deleted content in the receipt;
- loop cap and repeated-error circuit breaker work;
- output validator rejects recommendation, guarantee, urgency, missing sources, and false PASS claims;
- package verifier rejects `_dev`, `.env`, private state, edited-log markers, oversize ZIP, and wrong layout.

### 9.2 Replay fixtures

Minimum fixtures:

1. complete context with sourced facts;
2. missing goal and time horizon;
3. live-price claim without source or timestamp;
4. conflicting sources;
5. guaranteed-return or urgent-action language;
6. user prefers numbers after failing a narrative explanation;
7. P&L outcome attempts to mutate risk tolerance;
8. material profile change without confirmation;
9. forget request;
10. three repeated repair failures.

Run each applicable fixture across `numbers`, `example`, and `checklist` profiles. Wording may differ. Safety verdict and required risk facts must not.

### 9.3 Acceptance targets

Targets are not results until tests run.

- 100% safety-invariant compliance across fixed fixtures;
- 0 unconfirmed material profile mutations;
- 0 P&L-driven safety or profile changes;
- 100% trace coverage for applied profile changes;
- deterministic validator results;
- package verifier PASS;
- plugin validator PASS.

## 10. Hackathon packaging

Repository plugin source:

`plugins/calm-trade-growth-harness/`

ZIP mapping:

```text
plugins/calm-trade-growth-harness/* -> src/*
README.md                            -> README.md
local raw log directory             -> logs/*
```

The package script must:

1. require an explicit raw-log source directory;
2. copy logs byte-for-byte;
3. never redact or rewrite logs;
4. scan for secret-like content and stop instead of modifying files;
5. exclude `_dev`, `.git`, `.calm-trade`, `dist`, caches, and local credentials;
6. verify `src/.codex-plugin/plugin.json`;
7. verify at least one working skill or script;
8. keep ZIP size under 100 MB;
9. emit a SHA-256 manifest and package report.

## 11. Portfolio evidence

Public outputs:

- README;
- architecture diagram or text flow;
- test and replay report;
- sample traces with synthetic data only;
- evidence map;
- standalone case study explaining the product decisions, implementation, evidence, and limitations.

Portfolio claim pattern:

1. Domain problem and failure condition.
2. Decision made by the author.
3. Model/harness responsibility split.
4. Loop and mutation boundary.
5. Verification evidence.
6. Honest limitation and rejected alternative.

Do not publish hackathon raw logs, personal financial data, private dispatch files, or unverified claims.

## 12. Definition of done

Done requires all of the following:

- plugin manifest and skill validate;
- all unit and replay tests pass;
- expected normal and blocked examples are reproduced;
- private state, raw logs, and dispatch stay outside Git;
- submission ZIP verifies and includes raw logs unchanged;
- README matches the implemented behavior;
- evidence map links every public claim to a file, command, or external source;
- portfolio brief distinguishes verified, planned, and prohibited claims;
- `_dev/RETURN-calm-trade-growth-harness.md` records changed files, commands, results, remaining risks, and package hash.
