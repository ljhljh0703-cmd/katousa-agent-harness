from __future__ import annotations

import copy
import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

VALID_OUTPUT_STATUSES = {
    "READY_FOR_USER_DECISION",
    "BLOCKED_NEEDS_INFO",
    "BLOCKED_NEEDS_EVIDENCE",
    "BLOCKED_HUMAN_REVIEW",
}

STYLE_FORMATS = {"numbers", "example", "checklist", "dialogue"}
STYLE_LENGTHS = {"short", "balanced", "detailed"}
STYLE_VOCAB = {"beginner", "intermediate"}
QUESTION_DENSITY = {"low", "medium", "high"}
EVENT_TYPES = {
    "preference",
    "knowledge_check",
    "misunderstanding",
    "constraint",
    "profile_change",
    "deletion_receipt",
}
CONFIRMATION_STATES = {"candidate", "confirmed", "rejected", "not_required"}
DELTA_STATUSES = {"candidate", "confirmed", "rejected", "applied"}
DELTA_RISK_COLORS = {"green", "yellow", "red"}

MATERIAL_FIELDS = {
    "confirmed_decision_context.goal",
    "confirmed_decision_context.time_horizon",
    "confirmed_decision_context.loss_tolerance",
    "confirmed_decision_context.liquidity_need",
    "confirmed_decision_context.hard_constraints",
}

IMMUTABLE_FIELDS = {
    "schema_version",
    "profile_version",
    "updated_at",
    "safety_constitution_version",
    "output_schema_version",
    "safety_rules",
}

PROHIBITED_PATTERNS = {
    "recommendation": [
        r"\bshould buy\b",
        r"\bshould sell\b",
        r"\bjust buy\b",
        r"\bjust sell\b",
        r"매수하세요",
        r"매도하세요",
        r"지금 사",
        r"지금 팔",
    ],
    "guarantee": [
        r"\bguaranteed?\b",
        r"\bcertain(?:ty)?\b",
        r"확실한 수익",
        r"무조건",
        r"보장",
    ],
    "urgency": [
        r"\burgent\b",
        r"\bact now\b",
        r"\bimmediately\b",
        r"\btoo late\b",
        r"지금 아니면",
        r"서둘러",
        r"놓칠 수",
    ],
    "order_language": [
        r"\bplace an order\b",
        r"\bsubmit the trade\b",
        r"\bexecute\b",
        r"주문을 넣",
        r"체결",
    ],
    "fomo": [
        r"\bmiss out\b",
        r"\blast chance\b",
        r"기회를 놓칠",
    ],
}

SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"-----BEGIN [A-Z ]+PRIVATE KEY-----"),
]

BOUNDARY_SENTENCE = "이 결과는 판단을 돕는 설명 자료이며 종목 추천이나 주문 실행이 아닙니다."


class ValidationError(ValueError):
    """Raised when a strict contract is violated."""


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: str, payload: Any) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def append_jsonl(path: str, payload: dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def read_jsonl(path: str) -> list[dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return [json.loads(line) for line in handle if line.strip()]
    except FileNotFoundError:
        return []


def json_sha256(payload: Any) -> str:
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def file_sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(8192), b""):
            digest.update(chunk)
    return digest.hexdigest()


def assert_iso8601(value: Any, field_name: str) -> None:
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be an ISO-8601 string")
    try:
        if value.endswith("Z"):
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        else:
            datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be a valid ISO-8601 timestamp") from exc


def assert_no_secrets(value: str, field_name: str) -> None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(value):
            raise ValidationError(f"{field_name} contains secret-like content")


def is_public_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _require_fields(payload: dict[str, Any], fields: list[str], label: str) -> None:
    for field in fields:
        if field not in payload:
            raise ValidationError(f"{label} missing required field: {field}")


def _deep_get(payload: dict[str, Any], dotted_key: str) -> Any:
    cursor: Any = payload
    for part in dotted_key.split("."):
        if not isinstance(cursor, dict) or part not in cursor:
            raise ValidationError(f"unknown field path: {dotted_key}")
        cursor = cursor[part]
    return cursor


def _deep_set(payload: dict[str, Any], dotted_key: str, value: Any) -> dict[str, Any]:
    clone = copy.deepcopy(payload)
    cursor: Any = clone
    parts = dotted_key.split(".")
    for part in parts[:-1]:
        cursor = cursor[part]
    cursor[parts[-1]] = value
    return clone


def validate_profile(profile: dict[str, Any]) -> dict[str, Any]:
    _require_fields(
        profile,
        [
            "schema_version",
            "profile_version",
            "explanation_style",
            "confirmed_decision_context",
            "updated_at",
        ],
        "profile",
    )
    if profile["schema_version"] != "1.0":
        raise ValidationError("profile.schema_version must be '1.0'")
    if not isinstance(profile["profile_version"], int) or profile["profile_version"] < 1:
        raise ValidationError("profile.profile_version must be a positive integer")
    assert_iso8601(profile["updated_at"], "profile.updated_at")

    style = profile["explanation_style"]
    _require_fields(style, ["length", "format", "vocabulary", "question_density"], "explanation_style")
    if style["length"] not in STYLE_LENGTHS:
        raise ValidationError("explanation_style.length is invalid")
    if style["format"] not in STYLE_FORMATS:
        raise ValidationError("explanation_style.format is invalid")
    if style["vocabulary"] not in STYLE_VOCAB:
        raise ValidationError("explanation_style.vocabulary is invalid")
    if style["question_density"] not in QUESTION_DENSITY:
        raise ValidationError("explanation_style.question_density is invalid")

    context = profile["confirmed_decision_context"]
    _require_fields(
        context,
        ["goal", "time_horizon", "loss_tolerance", "liquidity_need", "hard_constraints"],
        "confirmed_decision_context",
    )
    if not isinstance(context["hard_constraints"], list):
        raise ValidationError("confirmed_decision_context.hard_constraints must be a list")
    return profile


def validate_event(event: dict[str, Any]) -> dict[str, Any]:
    _require_fields(
        event,
        [
            "id",
            "timestamp",
            "type",
            "source_turn",
            "content",
            "importance",
            "profile_version",
            "confirmation",
        ],
        "event",
    )
    if not re.fullmatch(r"evt_\d{4,}", event["id"]):
        raise ValidationError("event.id must match evt_0001")
    assert_iso8601(event["timestamp"], "event.timestamp")
    if event["type"] not in EVENT_TYPES:
        raise ValidationError("event.type is invalid")
    if not isinstance(event["content"], str) or not event["content"].strip():
        raise ValidationError("event.content must be a non-empty string")
    assert_no_secrets(event["content"], "event.content")
    if any(token in event["content"].lower() for token in ["account number", "api key", "password"]):
        raise ValidationError("event.content contains prohibited financial or credential payload")
    if not isinstance(event["importance"], int) or not 1 <= event["importance"] <= 5:
        raise ValidationError("event.importance must be an integer from 1 to 5")
    if not isinstance(event["profile_version"], int) or event["profile_version"] < 1:
        raise ValidationError("event.profile_version must be a positive integer")
    if event["confirmation"] not in CONFIRMATION_STATES:
        raise ValidationError("event.confirmation is invalid")
    return event


def validate_delta(delta: dict[str, Any], profile: dict[str, Any] | None = None) -> dict[str, Any]:
    _require_fields(
        delta,
        [
            "id",
            "field",
            "from",
            "to",
            "basis_event_ids",
            "risk_color",
            "requires_confirmation",
            "status",
            "created_at",
            "basis",
        ],
        "delta",
    )
    if not re.fullmatch(r"delta_\d{4,}", delta["id"]):
        raise ValidationError("delta.id must match delta_0001")
    if not isinstance(delta["field"], str):
        raise ValidationError("delta.field must be a string")
    if delta["field"] in IMMUTABLE_FIELDS:
        raise ValidationError("delta.field targets an immutable field")
    if delta["field"] == "confirmed_decision_context":
        raise ValidationError("delta.field must target exactly one field")
    if delta["field"] in {"explanation_style", "safety_rules"}:
        raise ValidationError("delta.field must target exactly one field")
    if isinstance(delta["to"], dict):
        raise ValidationError("delta.to must represent a single-field value, not an object")
    if not isinstance(delta["basis_event_ids"], list) or not delta["basis_event_ids"]:
        raise ValidationError("delta.basis_event_ids must be a non-empty list")
    if delta["risk_color"] not in DELTA_RISK_COLORS:
        raise ValidationError("delta.risk_color is invalid")
    if not isinstance(delta["requires_confirmation"], bool):
        raise ValidationError("delta.requires_confirmation must be boolean")
    if delta["status"] not in DELTA_STATUSES:
        raise ValidationError("delta.status is invalid")
    assert_iso8601(delta["created_at"], "delta.created_at")
    if not isinstance(delta["basis"], dict):
        raise ValidationError("delta.basis must be an object")
    if any("p&l" in str(value).lower() or "profit" in str(value).lower() for value in delta["basis"].values()):
        raise ValidationError("delta.basis must not use P&L as justification")
    if profile is not None:
        current_value = _deep_get(profile, delta["field"])
        if current_value != delta["from"]:
            raise ValidationError("delta.from does not match the current profile value")
        validate_profile(_deep_set(profile, delta["field"], delta["to"]))
    return delta


def validate_trace(trace: dict[str, Any]) -> dict[str, Any]:
    _require_fields(
        trace,
        [
            "trace_id",
            "input_id",
            "profile_name",
            "loaded_profile_version",
            "loaded_event_ids",
            "source_ledger",
            "validator_result",
            "confirmation_state",
            "stop_reason",
            "iteration_count",
            "error_signature",
            "immutable_safety_verdict",
        ],
        "trace",
    )
    if not re.fullmatch(r"trace_[a-f0-9]{12}", trace["trace_id"]):
        raise ValidationError("trace.trace_id is invalid")
    if not isinstance(trace["loaded_event_ids"], list):
        raise ValidationError("trace.loaded_event_ids must be a list")
    if not isinstance(trace["source_ledger"], list):
        raise ValidationError("trace.source_ledger must be a list")
    if not isinstance(trace["iteration_count"], int) or trace["iteration_count"] < 1:
        raise ValidationError("trace.iteration_count must be a positive integer")
    return trace


def validate_output_payload(output: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    required_fields = [
        "status",
        "request_summary",
        "missing_information",
        "sourced_facts",
        "interpretations",
        "unknowns_or_conflicts",
        "decision_paths",
        "personalized_explanation",
        "comprehension_check",
        "memory_candidate",
        "profile_delta_candidate",
        "safety_check_claim",
        "trace_id",
    ]
    for field in required_fields:
        if field not in output:
            errors.append(f"missing field: {field}")

    if errors:
        return {"ok": False, "errors": errors, "warnings": warnings}

    if output["status"] not in VALID_OUTPUT_STATUSES:
        errors.append("status is invalid")
    if BOUNDARY_SENTENCE not in str(output["personalized_explanation"]):
        errors.append("boundary sentence is missing from personalized_explanation")
    if not isinstance(output["missing_information"], list):
        errors.append("missing_information must be a list")
    if not isinstance(output["interpretations"], list) or not output["interpretations"]:
        errors.append("interpretations must be a non-empty list")
    if not isinstance(output["unknowns_or_conflicts"], list):
        errors.append("unknowns_or_conflicts must be a list")
    if not isinstance(output["decision_paths"], list) or not output["decision_paths"]:
        errors.append("decision_paths must be a non-empty list")
    if len(output["decision_paths"]) > 4:
        warnings.append("decision_paths is unusually large for the MVP")

    sourced_facts = output["sourced_facts"]
    if not isinstance(sourced_facts, list) or not sourced_facts:
        errors.append("sourced_facts must be a non-empty list")
    else:
        for index, fact in enumerate(sourced_facts):
            if not isinstance(fact, dict):
                errors.append(f"sourced_facts[{index}] must be an object")
                continue
            for key in ["claim", "source_url", "observed_at"]:
                if key not in fact:
                    errors.append(f"sourced_facts[{index}] missing {key}")
            if "source_url" in fact and not is_public_url(str(fact["source_url"])):
                errors.append(f"sourced_facts[{index}].source_url must be public http/https")
            if "observed_at" in fact:
                try:
                    assert_iso8601(fact["observed_at"], f"sourced_facts[{index}].observed_at")
                except ValidationError as exc:
                    errors.append(str(exc))

    decision_path_names = []
    for index, path in enumerate(output["decision_paths"]):
        if not isinstance(path, dict):
            errors.append(f"decision_paths[{index}] must be an object")
            continue
        for key in ["path_name", "conditions", "trade_offs", "what_would_change_the_path"]:
            if key not in path:
                errors.append(f"decision_paths[{index}] missing {key}")
        if "path_name" in path:
            decision_path_names.append(str(path["path_name"]))

    banned_text = json.dumps(output, ensure_ascii=False).lower()
    for category, patterns in PROHIBITED_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, banned_text, re.IGNORECASE):
                errors.append(f"prohibited {category} language detected")
                break

    claim = output["safety_check_claim"]
    if not isinstance(claim, dict):
        errors.append("safety_check_claim must be an object")
    else:
        validator_claim = str(claim.get("validator_verdict", "")).upper()
        evidence = claim.get("validator_evidence")
        if validator_claim == "PASS" and not evidence:
            errors.append("safety_check_claim cannot declare PASS without validator evidence")

    profile_delta = output["profile_delta_candidate"]
    delta_candidates = 0
    if profile_delta is None:
        delta_candidates = 0
    elif isinstance(profile_delta, dict):
        delta_candidates = 1
        try:
            validate_delta(profile_delta)
        except ValidationError as exc:
            errors.append(str(exc))
        if profile_delta.get("field") in MATERIAL_FIELDS and not profile_delta.get("requires_confirmation", False):
            errors.append("material profile delta must require confirmation")
    elif isinstance(profile_delta, list):
        delta_candidates = len(profile_delta)
        if len(profile_delta) > 1:
            errors.append("at most one profile delta candidate is allowed")
    else:
        errors.append("profile_delta_candidate must be null, object, or single-item list")

    if delta_candidates > 1:
        errors.append("at most one profile delta candidate is allowed")

    material_risk_present = any(
        "risk" in str(item).lower() or "loss" in str(item).lower() or "손실" in str(item)
        for item in sourced_facts + output["interpretations"] + output["unknowns_or_conflicts"]
    )
    if not material_risk_present:
        errors.append("material risk coverage is missing")

    uncertainty_present = bool(output["unknowns_or_conflicts"]) or any(
        "uncertain" in str(item).lower() or "unknown" in str(item).lower() or "불확실" in str(item)
        for item in output["interpretations"]
    )
    if not uncertainty_present:
        errors.append("explicit uncertainty coverage is missing")

    if not re.fullmatch(r"trace_[a-f0-9]{12}", str(output["trace_id"])):
        errors.append("trace_id is invalid")

    verdict = "PASS" if not errors else "FAIL"
    invariant_verdict = "PASS" if not any("material profile delta" in err for err in errors) else "FAIL"
    return {
        "ok": not errors,
        "verdict": verdict,
        "errors": errors,
        "warnings": warnings,
        "status": output["status"],
        "missing_material_information": output["missing_information"],
        "blocked_reason": output["status"] if output["status"] != "READY_FOR_USER_DECISION" else None,
        "required_risk_facts": [fact["claim"] for fact in sourced_facts if isinstance(fact, dict) and "claim" in fact],
        "decision_path_names": decision_path_names,
        "immutable_safety_verdict": invariant_verdict,
    }


def validate_case_fixture(case_payload: dict[str, Any]) -> dict[str, Any]:
    _require_fields(
        case_payload,
        [
            "case_id",
            "request",
            "status",
            "expected_status",
            "expected_invariant_verdict",
            "missing_information",
            "sourced_facts",
            "interpretations",
            "unknowns_or_conflicts",
            "decision_paths",
            "memory_candidate",
            "profile_delta_candidate",
            "comprehension_check",
            "source_ledger",
        ],
        "case_fixture",
    )
    if case_payload["status"] != case_payload["expected_status"]:
        raise ValidationError("fixture status and expected_status must match")
    if case_payload["expected_invariant_verdict"] not in {"PASS", "FAIL"}:
        raise ValidationError("fixture expected_invariant_verdict must be PASS or FAIL")
    return case_payload
