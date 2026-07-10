# State Model

## Immutable

- safety constitution version;
- output schema version;
- no-recommendation and no-execution boundary;
- source and audit requirements.

## Automatic candidate only

- preferred explanation length;
- preferred format: numbers, example, checklist, or dialogue;
- vocabulary level;
- question density;
- repeated misunderstanding tags.

These fields are not applied until the candidate passes validation. The final implementation may auto-apply low-risk style changes only when the public spec and tests explicitly allow it. The hackathon MVP should request confirmation.

## Confirmation required

- investment goal;
- time horizon;
- loss tolerance;
- liquidity need;
- leverage or concentration constraints;
- any rule that can materially alter the decision frame.

## Ephemeral

- current emotion;
- urgency;
- current asset or question;
- temporary source bundle.

Ephemeral fields expire after the run unless the user explicitly asks to save an allowed field.

## Memory event

```json
{
  "id": "evt_0001",
  "timestamp": "ISO-8601",
  "type": "preference|knowledge_check|misunderstanding|constraint|profile_change|deletion_receipt",
  "source_turn": "turn identifier",
  "content": "minimal non-secret content",
  "importance": 1,
  "profile_version": 1,
  "confirmation": "candidate|confirmed|rejected|not_required"
}
```
Events are append-only except that a forget operation removes the target payload and appends a deletion receipt without the deleted content.

## Profile delta

```json
{
  "field": "explanation_format",
  "from": "checklist",
  "to": "numbers",
  "basis_event_ids": ["evt_0001"],
  "risk_color": "green|yellow|red",
  "requires_confirmation": true,
  "status": "candidate|confirmed|rejected|applied"
}
```
