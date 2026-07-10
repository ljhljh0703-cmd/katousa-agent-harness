from __future__ import annotations

import copy
import hashlib
import os
import re
from pathlib import Path
from typing import Any

from .contracts import (
    MATERIAL_FIELDS,
    ValidationError,
    append_jsonl,
    json_sha256,
    now_iso,
    read_json,
    read_jsonl,
    validate_delta,
    validate_event,
    validate_profile,
    write_json,
)


def _state_paths(base_dir: str | Path) -> dict[str, Path]:
    root = Path(base_dir)
    return {
        "root": root,
        "profile": root / "profile.json",
        "events": root / "events.jsonl",
        "deltas": root / "profile-deltas.jsonl",
        "state": root / "state.json",
        "traces": root / "traces",
    }


def _next_id(prefix: str, rows: list[dict[str, Any]]) -> str:
    pattern = re.compile(rf"^{re.escape(prefix)}_(\d+)$")
    max_suffix = 0
    for row in rows:
        match = pattern.fullmatch(str(row.get("id", "")))
        if match:
            max_suffix = max(max_suffix, int(match.group(1)))
    return f"{prefix}_{max_suffix + 1:04d}"


def _profile_field_path(field: str) -> list[str]:
    return field.split(".")


def _get_field(profile: dict[str, Any], field: str) -> Any:
    cursor: Any = profile
    for part in _profile_field_path(field):
        cursor = cursor[part]
    return cursor


def _set_field(profile: dict[str, Any], field: str, value: Any) -> dict[str, Any]:
    clone = copy.deepcopy(profile)
    cursor: Any = clone
    parts = _profile_field_path(field)
    for part in parts[:-1]:
        cursor = cursor[part]
    cursor[parts[-1]] = value
    return clone


def default_profile(profile_format: str = "checklist") -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "profile_version": 1,
        "explanation_style": {
            "length": "balanced",
            "format": profile_format,
            "vocabulary": "beginner",
            "question_density": "medium",
        },
        "confirmed_decision_context": {
            "goal": None,
            "time_horizon": None,
            "loss_tolerance": None,
            "liquidity_need": None,
            "hard_constraints": [],
        },
        "updated_at": now_iso(),
    }


def init_state(base_dir: str | Path, profile: dict[str, Any] | None = None) -> dict[str, str]:
    paths = _state_paths(base_dir)
    paths["root"].mkdir(parents=True, exist_ok=True)
    paths["traces"].mkdir(parents=True, exist_ok=True)
    payload = validate_profile(profile or default_profile())
    write_json(str(paths["profile"]), payload)
    paths["events"].write_text("", encoding="utf-8")
    paths["deltas"].write_text("", encoding="utf-8")
    write_json(
        str(paths["state"]),
        {
            "active_run": None,
            "profile_version": payload["profile_version"],
            "iteration_count": 0,
            "last_error_signature": None,
            "same_error_count": 0,
            "rollback_pointer": None,
            "updated_at": now_iso(),
        },
    )
    return {name: str(path) for name, path in paths.items()}


def load_profile(base_dir: str | Path) -> dict[str, Any]:
    return validate_profile(read_json(str(_state_paths(base_dir)["profile"])))


def load_state_manifest(base_dir: str | Path) -> dict[str, Any]:
    return read_json(str(_state_paths(base_dir)["state"]))


def save_state_manifest(base_dir: str | Path, manifest: dict[str, Any]) -> None:
    manifest["updated_at"] = now_iso()
    write_json(str(_state_paths(base_dir)["state"]), manifest)


def record_event(
    base_dir: str | Path,
    *,
    event_type: str,
    source_turn: str,
    content: str,
    importance: int,
    confirmation: str,
) -> dict[str, Any]:
    paths = _state_paths(base_dir)
    profile = load_profile(base_dir)
    rows = read_jsonl(str(paths["events"]))
    event = {
        "id": _next_id("evt", rows),
        "timestamp": now_iso(),
        "type": event_type,
        "source_turn": source_turn,
        "content": content,
        "importance": importance,
        "profile_version": profile["profile_version"],
        "confirmation": confirmation,
    }
    validate_event(event)
    append_jsonl(str(paths["events"]), event)
    return event


def propose_delta(
    base_dir: str | Path,
    *,
    field: str,
    new_value: Any,
    basis_event_ids: list[str],
    basis_summary: str,
    basis_kind: str = "interaction_observation",
) -> dict[str, Any]:
    paths = _state_paths(base_dir)
    profile = load_profile(base_dir)
    rows = read_jsonl(str(paths["deltas"]))
    if "p&l" in basis_summary.lower() or "profit" in basis_summary.lower():
        raise ValidationError("P&L cannot create or justify a delta")
    current_value = _get_field(profile, field)
    requires_confirmation = True
    risk_color = "yellow" if field in MATERIAL_FIELDS else "green"
    delta = {
        "id": _next_id("delta", rows),
        "field": field,
        "from": current_value,
        "to": new_value,
        "basis_event_ids": basis_event_ids,
        "risk_color": risk_color,
        "requires_confirmation": requires_confirmation,
        "status": "candidate",
        "created_at": now_iso(),
        "basis": {
            "kind": basis_kind,
            "summary": basis_summary,
        },
    }
    validate_delta(delta, profile)
    append_jsonl(str(paths["deltas"]), delta)
    return delta


def reject_delta(base_dir: str | Path, *, delta_id: str, reason: str, source_turn: str) -> dict[str, Any]:
    paths = _state_paths(base_dir)
    deltas = read_jsonl(str(paths["deltas"]))
    for delta in deltas:
        if delta["id"] == delta_id:
            delta["status"] = "rejected"
            delta["rejected_at"] = now_iso()
            delta["rejection_reason"] = reason
            _rewrite_jsonl(str(paths["deltas"]), deltas)
            record_event(
                base_dir,
                event_type="profile_change",
                source_turn=source_turn,
                content=f"Rejected {delta_id}: {reason}",
                importance=2,
                confirmation="rejected",
            )
            return delta
    raise ValidationError(f"delta not found: {delta_id}")


def apply_delta(
    base_dir: str | Path,
    *,
    delta_id: str,
    source_turn: str,
    user_confirmation: bool,
    confirmation_evidence: str | None = None,
) -> dict[str, Any]:
    paths = _state_paths(base_dir)
    profile = load_profile(base_dir)
    deltas = read_jsonl(str(paths["deltas"]))
    for delta in deltas:
        if delta["id"] != delta_id:
            continue
        validate_delta(delta, profile)
        if not user_confirmation:
            raise ValidationError("apply requires explicit user confirmation")
        if delta["field"] in MATERIAL_FIELDS and not confirmation_evidence:
            raise ValidationError("material profile changes require confirmation evidence")
        new_profile = _set_field(profile, delta["field"], delta["to"])
        new_profile["profile_version"] = profile["profile_version"] + 1
        new_profile["updated_at"] = now_iso()
        validate_profile(new_profile)
        write_json(str(paths["profile"]), new_profile)
        delta["status"] = "applied"
        delta["applied_at"] = now_iso()
        delta["confirmation_evidence"] = confirmation_evidence
        _rewrite_jsonl(str(paths["deltas"]), deltas)
        event = record_event(
            base_dir,
            event_type="profile_change",
            source_turn=source_turn,
            content=f"Applied {delta_id} to {delta['field']}",
            importance=3,
            confirmation="confirmed",
        )
        manifest = load_state_manifest(base_dir)
        manifest["profile_version"] = new_profile["profile_version"]
        manifest["rollback_pointer"] = json_sha256(profile)
        save_state_manifest(base_dir, manifest)
        return {"delta": delta, "profile": new_profile, "audit_event": event}
    raise ValidationError(f"delta not found: {delta_id}")


def forget_event_payload(base_dir: str | Path, *, event_id: str, source_turn: str) -> dict[str, Any]:
    paths = _state_paths(base_dir)
    events = read_jsonl(str(paths["events"]))
    remaining = []
    deleted_event = None
    for event in events:
        if event["id"] == event_id:
            deleted_event = event
            continue
        remaining.append(event)
    if deleted_event is None:
        raise ValidationError(f"event not found: {event_id}")
    _rewrite_jsonl(str(paths["events"]), remaining)
    receipt = {
        "id": _next_id("evt", events),
        "timestamp": now_iso(),
        "type": "deletion_receipt",
        "source_turn": source_turn,
        "content": f"Deleted payload hash {hashlib.sha256(deleted_event['content'].encode('utf-8')).hexdigest()} for {event_id}",
        "importance": 2,
        "profile_version": load_profile(base_dir)["profile_version"],
        "confirmation": "not_required",
        "deleted_event_id": event_id,
        "deleted_payload_hash": hashlib.sha256(deleted_event["content"].encode("utf-8")).hexdigest(),
    }
    validate_event(receipt)
    append_jsonl(str(paths["events"]), receipt)
    return receipt


def update_run_state(
    base_dir: str | Path,
    *,
    active_run: str,
    error_signature: str | None,
) -> dict[str, Any]:
    manifest = load_state_manifest(base_dir)
    manifest["active_run"] = active_run
    manifest["iteration_count"] = int(manifest.get("iteration_count", 0)) + 1
    prior_error = manifest.get("last_error_signature")
    if error_signature and error_signature == prior_error:
        manifest["same_error_count"] = int(manifest.get("same_error_count", 0)) + 1
    elif error_signature:
        manifest["same_error_count"] = 1
    else:
        manifest["same_error_count"] = 0
    manifest["last_error_signature"] = error_signature
    save_state_manifest(base_dir, manifest)
    return manifest


def loop_gate(manifest: dict[str, Any], cap: int = 3) -> dict[str, Any]:
    if int(manifest.get("same_error_count", 0)) >= cap:
        return {"blocked": True, "reason": "REPEATED_ERROR_CIRCUIT_BREAKER"}
    if int(manifest.get("iteration_count", 0)) >= cap:
        return {"blocked": True, "reason": "LOOP_CAP_REACHED"}
    return {"blocked": False, "reason": None}


def _rewrite_jsonl(path: str, rows: list[dict[str, Any]]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(__import__("json").dumps(row, ensure_ascii=False) + "\n")
