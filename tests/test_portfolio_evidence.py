from __future__ import annotations

import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_ROOT = os.path.join(REPO_ROOT, "scripts")
if SCRIPTS_ROOT not in sys.path:
    sys.path.insert(0, SCRIPTS_ROOT)

from export_portfolio_evidence import build_portfolio_evidence  # noqa: E402


class PortfolioEvidenceTests(unittest.TestCase):
    def test_export_preserves_replay_summary_and_profile_invariants(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            evidence = build_portfolio_evidence(
                os.path.join(REPO_ROOT, "fixtures"),
                os.path.join(tmp_dir, "portfolio-evidence.json"),
            )

        summary = evidence["replay_summary"]
        self.assertEqual(summary["total_runs"], 30)
        self.assertEqual(summary["pass_count"], 15)
        self.assertEqual(summary["expected_fail_count"], 15)
        self.assertEqual(summary["invariant_mismatch_count"], 0)
        self.assertTrue(summary["all_invariants_stable"])

        comparison = evidence["same_case_three_explanation_profiles"]
        self.assertEqual(len(comparison), 3)
        self.assertEqual({row["validator_verdict"] for row in comparison}, {"PASS"})
        self.assertEqual({row["immutable_safety_verdict"] for row in comparison}, {"PASS"})
        self.assertEqual(len({row["personalized_explanation"] for row in comparison}), 3)

    def test_export_keeps_block_and_confirmation_boundaries_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            evidence = build_portfolio_evidence(
                os.path.join(REPO_ROOT, "fixtures"),
                os.path.join(tmp_dir, "portfolio-evidence.json"),
            )

        blocked = evidence["blocked_without_current_source"]
        self.assertEqual(blocked["status"], "BLOCKED_NEEDS_EVIDENCE")
        self.assertEqual(blocked["blocked_reason"], "BLOCKED_NEEDS_EVIDENCE")
        self.assertEqual(blocked["immutable_safety_verdict"], "PASS")

        change = evidence["unconfirmed_material_change"]
        self.assertEqual(change["validator_verdict"], "FAIL")
        self.assertTrue(change["requires_confirmation"])
        self.assertEqual(change["confirmation_state"], "required")
        self.assertEqual(change["candidate_field"], "confirmed_decision_context.time_horizon")


if __name__ == "__main__":
    unittest.main()
