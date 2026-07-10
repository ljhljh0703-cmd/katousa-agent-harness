from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugins" / "calm-trade-growth-harness"
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from calm_trade_growth_harness.replay import run_replay_eval  # noqa: E402


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def _pick(traces: list[dict[str, Any]], case_id: str, profile_name: str) -> dict[str, Any]:
    for trace in traces:
        if trace["input_id"] == case_id and trace["profile_name"] == profile_name:
            return trace
    raise RuntimeError(f"portfolio evidence trace not found: {case_id}/{profile_name}")


def build_portfolio_evidence(fixtures_root: str | Path, output_path: str | Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        metrics = run_replay_eval(fixtures_root, tmp_dir)
        traces = _load_jsonl(Path(tmp_dir) / "replay-trace.jsonl")

    comparison = []
    for profile_name in ["default_checklist", "example_profile", "numbers_profile"]:
        trace = _pick(traces, "complete_sourced_question", profile_name)
        comparison.append(
            {
                "profile_name": profile_name,
                "status": trace["validator_result"]["status"],
                "validator_verdict": trace["validator_result"]["verdict"],
                "immutable_safety_verdict": trace["immutable_safety_verdict"],
                "personalized_explanation": trace["generated_output"]["personalized_explanation"],
            }
        )

    blocked = _pick(traces, "live_claim_without_source", "default_checklist")
    controlled_change = _pick(traces, "material_change_without_confirmation", "default_checklist")
    delta = controlled_change["generated_output"]["profile_delta_candidate"]

    evidence = {
        "schema_version": "1.0",
        "artifact": "카투사 포트폴리오 프로세스 증거",
        "generated_from": "fresh fixture replay via scripts/export_portfolio_evidence.py",
        "generated_at": metrics["generated_at"],
        "process_metrics_only": True,
        "replay_summary": {
            "total_runs": metrics["total_runs"],
            "pass_count": metrics["pass_count"],
            "expected_fail_count": metrics["fail_count"],
            "invariant_mismatch_count": len(metrics["invariant_mismatches"]),
            "all_invariants_stable": metrics["all_invariants_stable"],
            "profiles": metrics["profiles"],
            "cases": metrics["cases"],
        },
        "same_case_three_explanation_profiles": comparison,
        "blocked_without_current_source": {
            "request_summary": blocked["generated_output"]["request_summary"],
            "status": blocked["validator_result"]["status"],
            "missing_information": blocked["validator_result"]["missing_material_information"],
            "blocked_reason": blocked["validator_result"]["blocked_reason"],
            "immutable_safety_verdict": blocked["immutable_safety_verdict"],
        },
        "unconfirmed_material_change": {
            "request_summary": controlled_change["generated_output"]["request_summary"],
            "status": controlled_change["validator_result"]["status"],
            "validator_verdict": controlled_change["validator_result"]["verdict"],
            "validator_errors": controlled_change["validator_result"]["errors"],
            "candidate_field": delta["field"],
            "requires_confirmation": delta["requires_confirmation"],
            "confirmation_state": controlled_change["confirmation_state"],
            "immutable_safety_verdict": controlled_change["immutable_safety_verdict"],
        },
        "claim_boundaries": [
            "투자 성과나 수익률을 측정하지 않았다.",
            "실제 사용자의 이해도 향상을 측정하지 않았다.",
            "카카오페이증권 공식 제품·연동·보증이 아니다.",
            "법률·컴플라이언스 적합성 인증이 아니다.",
        ],
    }

    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a small, public-safe portfolio evidence snapshot.")
    parser.add_argument("--fixtures", default=str(REPO_ROOT / "fixtures"))
    parser.add_argument("--out", default=str(REPO_ROOT / "docs" / "portfolio-evidence.json"))
    args = parser.parse_args()
    evidence = build_portfolio_evidence(args.fixtures, args.out)
    print(json.dumps(evidence["replay_summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
