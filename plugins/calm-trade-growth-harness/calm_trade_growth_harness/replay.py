from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .contracts import (
    BOUNDARY_SENTENCE,
    ValidationError,
    append_jsonl,
    now_iso,
    read_json,
    validate_case_fixture,
    validate_output_payload,
)


def _trace_id(case_id: str, profile_name: str) -> str:
    return "trace_" + hashlib.sha256(f"{case_id}:{profile_name}".encode("utf-8")).hexdigest()[:12]


def _render_explanation(profile: dict[str, Any], case_payload: dict[str, Any]) -> str:
    variant = profile["explanation_style"]["format"]
    core = case_payload["explanation_core"]
    if variant == "numbers":
        lines = [
            "1. 확인된 사실: " + core["facts"],
            "2. 해석: " + core["interpretation"],
            "3. 남은 불확실성: " + core["unknowns"],
            "4. 다음 확인 질문: " + core["next_step"],
            BOUNDARY_SENTENCE,
        ]
    elif variant == "example":
        lines = [
            "예시로 보면, " + core["example"],
            "핵심 사실은 " + core["facts"],
            "해석은 " + core["interpretation"],
            "아직 남은 불확실성은 " + core["unknowns"],
            BOUNDARY_SENTENCE,
        ]
    else:
        lines = [
            "- 사실: " + core["facts"],
            "- 해석: " + core["interpretation"],
            "- 남은 불확실성: " + core["unknowns"],
            "- 다음 확인: " + core["next_step"],
            BOUNDARY_SENTENCE,
        ]
    return "\n".join(lines)


def build_output(case_payload: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": case_payload["status"],
        "request_summary": case_payload["request"],
        "missing_information": case_payload["missing_information"],
        "sourced_facts": case_payload["sourced_facts"],
        "interpretations": case_payload["interpretations"],
        "unknowns_or_conflicts": case_payload["unknowns_or_conflicts"],
        "decision_paths": case_payload["decision_paths"],
        "personalized_explanation": _render_explanation(profile, case_payload),
        "comprehension_check": case_payload["comprehension_check"],
        "memory_candidate": case_payload["memory_candidate"],
        "profile_delta_candidate": case_payload["profile_delta_candidate"],
        "safety_check_claim": {
            "validator_verdict": "NOT_RUN",
            "validator_evidence": None,
        },
        "trace_id": _trace_id(case_payload["case_id"], profile["name"]),
    }


def run_replay_eval(fixtures_root: str | Path, out_dir: str | Path) -> dict[str, Any]:
    fixtures_path = Path(fixtures_root)
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    profiles = [read_json(str(path)) for path in sorted((fixtures_path / "profiles").glob("*.json"))]
    cases = [read_json(str(path)) for path in sorted((fixtures_path / "cases").glob("*.json"))]
    for case_payload in cases:
        validate_case_fixture(case_payload)

    traces: list[dict[str, Any]] = []
    invariant_groups: dict[str, list[dict[str, Any]]] = {}

    for case_payload in cases:
        applicable = set(case_payload.get("applicable_profiles", [])) or {profile["name"] for profile in profiles}
        for profile in profiles:
            if profile["name"] not in applicable:
                continue
            output = build_output(case_payload, profile)
            result = validate_output_payload(output)
            trace = {
                "trace_id": output["trace_id"],
                "input_id": case_payload["case_id"],
                "profile_name": profile["name"],
                "loaded_profile_version": profile["profile_version"],
                "loaded_event_ids": case_payload.get("loaded_event_ids", []),
                "source_ledger": case_payload["source_ledger"],
                "generated_output": output,
                "validator_result": result,
                "confirmation_state": "required" if output["profile_delta_candidate"] else "not_required",
                "stop_reason": result["blocked_reason"],
                "iteration_count": case_payload.get("iteration_count", 1),
                "error_signature": case_payload.get("error_signature"),
                "immutable_safety_verdict": result["immutable_safety_verdict"],
                "process_metrics_only": True,
                "generated_at": now_iso(),
            }
            traces.append(trace)
            invariant_groups.setdefault(case_payload["case_id"], []).append(
                {
                    "profile_name": profile["name"],
                    "status": result["status"],
                    "missing_material_information": result["missing_material_information"],
                    "required_risk_facts": result["required_risk_facts"],
                    "blocked_reason": result["blocked_reason"],
                    "immutable_safety_verdict": result["immutable_safety_verdict"],
                    "verdict": result["verdict"],
                }
            )

    mismatches = []
    for case_id, rows in invariant_groups.items():
        baseline = None
        for row in rows:
            comparable = {
                "status": row["status"],
                "missing_material_information": row["missing_material_information"],
                "required_risk_facts": row["required_risk_facts"],
                "blocked_reason": row["blocked_reason"],
                "immutable_safety_verdict": row["immutable_safety_verdict"],
            }
            if baseline is None:
                baseline = comparable
                continue
            if comparable != baseline:
                mismatches.append({"case_id": case_id, "row": row, "baseline": baseline})

    pass_count = sum(1 for trace in traces if trace["validator_result"]["ok"])
    fail_count = len(traces) - pass_count
    report = {
        "generated_at": now_iso(),
        "process_metrics_only": True,
        "profiles": [profile["name"] for profile in profiles],
        "cases": [case["case_id"] for case in cases],
        "total_runs": len(traces),
        "pass_count": pass_count,
        "fail_count": fail_count,
        "invariant_mismatches": mismatches,
        "all_invariants_stable": not mismatches,
        "deterministic_validator": True,
    }

    metrics_path = out_path / "replay-metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    trace_path = out_path / "replay-trace.jsonl"
    trace_path.write_text("", encoding="utf-8")
    for trace in traces:
        append_jsonl(str(trace_path), trace)

    report_path = out_path / "replay-report.md"
    lines = [
        "# Replay Report",
        "",
        "This report measures process and safety metrics only. It does not claim investment performance.",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Total runs: `{report['total_runs']}`",
        f"- PASS: `{report['pass_count']}`",
        f"- FAIL: `{report['fail_count']}`",
        f"- Stable safety invariants across profiles: `{report['all_invariants_stable']}`",
        "",
        "## Case Matrix",
        "",
    ]
    for case_id, rows in invariant_groups.items():
        lines.append(f"### {case_id}")
        for row in rows:
            lines.append(
                f"- {row['profile_name']}: validator `{row['verdict']}`, status `{row['status']}`, immutable safety `{row['immutable_safety_verdict']}`"
            )
    if mismatches:
        lines.extend(["", "## Invariant mismatches", ""])
        for mismatch in mismatches:
            lines.append(f"- {mismatch['case_id']}: {json.dumps(mismatch, ensure_ascii=False)}")
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    if mismatches:
        raise ValidationError("safety invariants diverged across profiles")
    return report
