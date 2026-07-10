from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_ROOT = os.path.join(REPO_ROOT, "plugins", "calm-trade-growth-harness")
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from calm_trade_growth_harness.contracts import (  # noqa: E402
    ValidationError,
    read_json,
    validate_case_fixture,
    validate_output_payload,
    validate_profile,
)


class ContractFixtureTests(unittest.TestCase):
    def test_profiles_parse(self) -> None:
        profiles_dir = os.path.join(REPO_ROOT, "fixtures", "profiles")
        for name in os.listdir(profiles_dir):
            profile = read_json(os.path.join(profiles_dir, name))
            self.assertEqual(validate_profile(profile)["schema_version"], "1.0")

    def test_cases_parse(self) -> None:
        cases_dir = os.path.join(REPO_ROOT, "fixtures", "cases")
        case_names = sorted(os.listdir(cases_dir))
        self.assertEqual(len(case_names), 10)
        for name in case_names:
            case_payload = read_json(os.path.join(cases_dir, name))
            validated = validate_case_fixture(case_payload)
            self.assertEqual(validated["status"], validated["expected_status"])

    def test_invalid_profile_reason_is_specific(self) -> None:
        profile = read_json(os.path.join(REPO_ROOT, "fixtures", "profiles", "default_checklist.json"))
        profile["explanation_style"]["format"] = "essay"
        with self.assertRaisesRegex(ValidationError, "explanation_style.format is invalid"):
            validate_profile(profile)

    def test_output_validator_accepts_valid_fixture(self) -> None:
        payload = read_json(os.path.join(REPO_ROOT, "fixtures", "outputs", "valid_ready_output.json"))
        result = validate_output_payload(payload)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["verdict"], "PASS")

    def test_output_validator_rejects_false_pass_and_guarantee_language(self) -> None:
        payload = read_json(os.path.join(REPO_ROOT, "fixtures", "outputs", "invalid_guarantee_output.json"))
        result = validate_output_payload(payload)
        self.assertFalse(result["ok"])
        self.assertIn("prohibited guarantee language detected", result["errors"])
        self.assertIn(
            "safety_check_claim cannot declare PASS without validator evidence",
            result["errors"],
        )

    def test_output_validator_rejects_missing_source_timestamp(self) -> None:
        payload = read_json(os.path.join(REPO_ROOT, "fixtures", "outputs", "valid_ready_output.json"))
        del payload["sourced_facts"][0]["observed_at"]
        result = validate_output_payload(payload)
        self.assertFalse(result["ok"])
        self.assertIn("sourced_facts[0] missing observed_at", result["errors"])

    def test_output_validator_rejects_recommendation_language(self) -> None:
        payload = read_json(os.path.join(REPO_ROOT, "fixtures", "outputs", "valid_ready_output.json"))
        payload["personalized_explanation"] = (
            "You should buy now.\n"
            "이 결과는 판단을 돕는 설명 자료이며 종목 추천이나 주문 실행이 아닙니다."
        )
        result = validate_output_payload(payload)
        self.assertFalse(result["ok"])
        self.assertIn("prohibited recommendation language detected", result["errors"])


if __name__ == "__main__":
    unittest.main()
