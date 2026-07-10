from __future__ import annotations

import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_ROOT = os.path.join(REPO_ROOT, "plugins", "calm-trade-growth-harness")
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from calm_trade_growth_harness.contracts import read_jsonl, ValidationError  # noqa: E402
from calm_trade_growth_harness.state import (  # noqa: E402
    apply_delta,
    default_profile,
    forget_event_payload,
    init_state,
    load_profile,
    load_state_manifest,
    loop_gate,
    propose_delta,
    record_event,
    update_run_state,
)


class StateRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = os.path.join(self.temp_dir.name, ".calm-trade")
        init_state(self.state_dir, default_profile())

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_event_store_appends_and_preserves_provenance(self) -> None:
        first = record_event(
            self.state_dir,
            event_type="preference",
            source_turn="turn-1",
            content="숫자형 설명 선호",
            importance=2,
            confirmation="candidate",
        )
        second = record_event(
            self.state_dir,
            event_type="knowledge_check",
            source_turn="turn-2",
            content="손실 가능성을 다시 설명함",
            importance=3,
            confirmation="not_required",
        )
        rows = read_jsonl(os.path.join(self.state_dir, "events.jsonl"))
        self.assertEqual(rows[0]["id"], first["id"])
        self.assertEqual(rows[1]["source_turn"], second["source_turn"])

    def test_no_silent_update_until_apply(self) -> None:
        event = record_event(
            self.state_dir,
            event_type="preference",
            source_turn="turn-1",
            content="숫자형 설명 선호",
            importance=2,
            confirmation="candidate",
        )
        delta = propose_delta(
            self.state_dir,
            field="explanation_style.format",
            new_value="numbers",
            basis_event_ids=[event["id"]],
            basis_summary="사용자가 숫자형 설명을 명시적으로 요청했다.",
        )
        profile = load_profile(self.state_dir)
        self.assertEqual(profile["profile_version"], 1)
        self.assertEqual(profile["explanation_style"]["format"], "checklist")
        self.assertEqual(delta["status"], "candidate")

    def test_one_change_rule_rejects_multi_field_delta(self) -> None:
        event = record_event(
            self.state_dir,
            event_type="preference",
            source_turn="turn-1",
            content="설명 스타일 전체를 바꿔 달라고 요청함",
            importance=2,
            confirmation="candidate",
        )
        with self.assertRaisesRegex(ValidationError, "must target exactly one field"):
            propose_delta(
                self.state_dir,
                field="explanation_style",
                new_value={"format": "numbers", "length": "short"},
                basis_event_ids=[event["id"]],
                basis_summary="여러 스타일 값을 한 번에 바꾸려는 시도",
            )

    def test_material_apply_requires_confirmation_evidence(self) -> None:
        event = record_event(
            self.state_dir,
            event_type="constraint",
            source_turn="turn-1",
            content="투자 기간을 1년으로 바꾸고 싶다고 말함",
            importance=3,
            confirmation="candidate",
        )
        delta = propose_delta(
            self.state_dir,
            field="confirmed_decision_context.time_horizon",
            new_value="1 year",
            basis_event_ids=[event["id"]],
            basis_summary="사용자가 기간 변경을 요청했다.",
        )
        with self.assertRaisesRegex(ValidationError, "confirmation evidence"):
            apply_delta(
                self.state_dir,
                delta_id=delta["id"],
                source_turn="turn-2",
                user_confirmation=True,
            )

    def test_apply_increments_version_and_writes_audit_event(self) -> None:
        event = record_event(
            self.state_dir,
            event_type="preference",
            source_turn="turn-1",
            content="숫자형 설명을 원함",
            importance=2,
            confirmation="candidate",
        )
        delta = propose_delta(
            self.state_dir,
            field="explanation_style.format",
            new_value="numbers",
            basis_event_ids=[event["id"]],
            basis_summary="사용자가 숫자형 설명을 요청했다.",
        )
        result = apply_delta(
            self.state_dir,
            delta_id=delta["id"],
            source_turn="turn-2",
            user_confirmation=True,
            confirmation_evidence="사용자 확인: 숫자형 설명으로 저장해 주세요.",
        )
        self.assertEqual(result["profile"]["profile_version"], 2)
        self.assertEqual(result["profile"]["explanation_style"]["format"], "numbers")
        rows = read_jsonl(os.path.join(self.state_dir, "events.jsonl"))
        self.assertEqual(rows[-1]["type"], "profile_change")
        manifest = load_state_manifest(self.state_dir)
        self.assertEqual(manifest["profile_version"], 2)
        self.assertIsNotNone(manifest["rollback_pointer"])

    def test_pnl_cannot_justify_delta(self) -> None:
        event = record_event(
            self.state_dir,
            event_type="constraint",
            source_turn="turn-1",
            content="지난번 수익이 났다고 말함",
            importance=1,
            confirmation="candidate",
        )
        with self.assertRaisesRegex(ValidationError, "P&L cannot create or justify a delta"):
            propose_delta(
                self.state_dir,
                field="confirmed_decision_context.loss_tolerance",
                new_value="high",
                basis_event_ids=[event["id"]],
                basis_summary="P&L profit proves the user can take more risk",
            )

    def test_forget_removes_payload_and_keeps_only_receipt(self) -> None:
        event = record_event(
            self.state_dir,
            event_type="preference",
            source_turn="turn-1",
            content="삭제될 선호 문장",
            importance=2,
            confirmation="candidate",
        )
        receipt = forget_event_payload(self.state_dir, event_id=event["id"], source_turn="turn-2")
        rows = read_jsonl(os.path.join(self.state_dir, "events.jsonl"))
        joined = "\n".join(row["content"] for row in rows)
        self.assertNotIn("삭제될 선호 문장", joined)
        self.assertEqual(rows[-1]["type"], "deletion_receipt")
        self.assertEqual(rows[-1]["deleted_event_id"], event["id"])
        self.assertIn(receipt["deleted_payload_hash"], rows[-1]["content"])
        self.assertEqual(rows[-1]["id"], "evt_0002")

    def test_forget_after_apply_keeps_event_ids_unique_and_monotonic(self) -> None:
        first = record_event(
            self.state_dir,
            event_type="preference",
            source_turn="turn-1",
            content="삭제될 선호 문장",
            importance=2,
            confirmation="candidate",
        )
        delta = propose_delta(
            self.state_dir,
            field="explanation_style.format",
            new_value="numbers",
            basis_event_ids=[first["id"]],
            basis_summary="사용자가 숫자형 설명을 요청했다.",
        )
        apply_delta(
            self.state_dir,
            delta_id=delta["id"],
            source_turn="turn-2",
            user_confirmation=True,
            confirmation_evidence="사용자 확인: 숫자형 설명으로 저장해 주세요.",
        )

        receipt = forget_event_payload(self.state_dir, event_id=first["id"], source_turn="turn-3")
        next_event = record_event(
            self.state_dir,
            event_type="knowledge_check",
            source_turn="turn-4",
            content="다음 점검 질문",
            importance=2,
            confirmation="not_required",
        )

        rows = read_jsonl(os.path.join(self.state_dir, "events.jsonl"))
        self.assertEqual(receipt["id"], "evt_0003")
        self.assertEqual(next_event["id"], "evt_0004")
        self.assertEqual([row["id"] for row in rows], ["evt_0002", "evt_0003", "evt_0004"])
        self.assertEqual(rows[1]["deleted_event_id"], first["id"])
        self.assertNotIn("삭제될 선호 문장", "\n".join(row["content"] for row in rows))

    def test_forget_highest_event_keeps_event_ids_unique_and_monotonic(self) -> None:
        first = record_event(
            self.state_dir,
            event_type="preference",
            source_turn="turn-1",
            content="유지되는 선호 문장",
            importance=2,
            confirmation="candidate",
        )
        second = record_event(
            self.state_dir,
            event_type="knowledge_check",
            source_turn="turn-2",
            content="삭제될 두 번째 이벤트",
            importance=2,
            confirmation="not_required",
        )

        receipt = forget_event_payload(self.state_dir, event_id=second["id"], source_turn="turn-3")
        next_event = record_event(
            self.state_dir,
            event_type="constraint",
            source_turn="turn-4",
            content="다음 제약 확인",
            importance=2,
            confirmation="candidate",
        )

        rows = read_jsonl(os.path.join(self.state_dir, "events.jsonl"))
        self.assertEqual(first["id"], "evt_0001")
        self.assertEqual(second["id"], "evt_0002")
        self.assertEqual(receipt["id"], "evt_0003")
        self.assertEqual(next_event["id"], "evt_0004")
        self.assertEqual([row["id"] for row in rows], ["evt_0001", "evt_0003", "evt_0004"])
        self.assertEqual(rows[1]["deleted_event_id"], second["id"])
        self.assertNotIn("삭제될 두 번째 이벤트", "\n".join(row["content"] for row in rows))

    def test_loop_cap_and_repeated_error_circuit_breaker(self) -> None:
        manifest = None
        for signature in ["missing_sources", "missing_goal", "missing_timestamp"]:
            manifest = update_run_state(self.state_dir, active_run="trace_test", error_signature=signature)
        assert manifest is not None
        gate = loop_gate(manifest, cap=3)
        self.assertTrue(gate["blocked"])
        self.assertEqual(gate["reason"], "LOOP_CAP_REACHED")

        init_state(self.state_dir, default_profile())
        for _ in range(3):
            manifest = update_run_state(self.state_dir, active_run="trace_test", error_signature="same_error")
        gate = loop_gate(manifest, cap=3)
        self.assertTrue(gate["blocked"])
        self.assertEqual(gate["reason"], "REPEATED_ERROR_CIRCUIT_BREAKER")


if __name__ == "__main__":
    unittest.main()
