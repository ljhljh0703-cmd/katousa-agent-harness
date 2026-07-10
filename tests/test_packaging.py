from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from submission_lib import SubmissionError, build_submission, verify_submission  # noqa: E402


class PackagingTests(unittest.TestCase):
    def test_build_and_verify_test_only_package(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "test-submission.zip"
            result = build_submission(
                str(REPO_ROOT / "fixtures" / "test-logs"),
                str(out_path),
                test_only=True,
            )
            self.assertTrue(out_path.exists())
            self.assertTrue(result["test_only"])

            source_log = REPO_ROOT / "fixtures" / "test-logs" / "turns.jsonl"
            with zipfile.ZipFile(out_path, "r") as archive:
                packaged_bytes = archive.read("logs/turns.jsonl")
            self.assertEqual(source_log.read_bytes(), packaged_bytes)

            verified = verify_submission(str(out_path), allow_test_only=True)
            self.assertTrue(verified["ok"])

    def test_build_rejects_secret_like_log_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = Path(temp_dir) / "logs"
            logs_dir.mkdir()
            fake_key = "token=" + "s" + "k-" + "1234567890abcdef1234" + "\n"
            (logs_dir / "secret.txt").write_text(fake_key, encoding="utf-8")
            with self.assertRaisesRegex(SubmissionError, r"secret\.txt:1 \[openai_api_key\]"):
                build_submission(str(logs_dir), str(Path(temp_dir) / "submission.zip"), test_only=True)

    def test_build_accepts_jsonl_command_that_mentions_edit_markers(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = Path(temp_dir) / "logs"
            logs_dir.mkdir()
            command_log = {"item": {"command": "scan EDITED_LOG and [REDACTED] markers"}}
            source_path = logs_dir / "commands.jsonl"
            source_path.write_text(json.dumps(command_log) + "\n", encoding="utf-8")
            out_path = Path(temp_dir) / "submission.zip"

            build_submission(str(logs_dir), str(out_path), test_only=True)

            with zipfile.ZipFile(out_path, "r") as archive:
                self.assertEqual(source_path.read_bytes(), archive.read("logs/commands.jsonl"))
            self.assertTrue(verify_submission(str(out_path), allow_test_only=True)["ok"])

    def test_build_rejects_jsonl_edit_marker_outside_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            logs_dir = Path(temp_dir) / "logs"
            logs_dir.mkdir()
            edited_log = {"item": {"output": "[REDACTED]"}}
            (logs_dir / "edited.jsonl").write_text(json.dumps(edited_log) + "\n", encoding="utf-8")

            with self.assertRaisesRegex(SubmissionError, r"edited\.jsonl:1 \[edited_log_marker\]"):
                build_submission(str(logs_dir), str(Path(temp_dir) / "submission.zip"), test_only=True)

    def test_verify_rejects_wrong_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "broken.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("README.md", "readme")
                archive.writestr("logs/run.txt", "log")
            (Path(temp_dir) / "SHA256SUMS.txt").write_text("", encoding="utf-8")
            (Path(temp_dir) / "package-report.md").write_text("- Secret scan: `PASS`\n", encoding="utf-8")
            with self.assertRaisesRegex(SubmissionError, "src/.codex-plugin/plugin.json"):
                verify_submission(str(archive_path), allow_test_only=True)

    def test_verify_rejects_forbidden_path_and_edited_log_marker(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_path = Path(temp_dir) / "bad.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("README.md", "readme")
                archive.writestr("src/.codex-plugin/plugin.json", "{}")
                archive.writestr("src/scripts/tool.py", "print('ok')")
                archive.writestr("logs/run.txt", "EDITED_LOG\n")
                archive.writestr("src/.env", "oops")
            (Path(temp_dir) / "SHA256SUMS.txt").write_text("", encoding="utf-8")
            (Path(temp_dir) / "package-report.md").write_text(
                "- Secret scan: `PASS`\n- Package label: `TEST_ONLY`\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(SubmissionError, r"forbidden path found in archive: src/\.env"):
                verify_submission(str(archive_path), allow_test_only=True)

    def test_verify_rejects_oversize_limit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "test-submission.zip"
            build_submission(str(REPO_ROOT / "fixtures" / "test-logs"), str(out_path), test_only=True)
            with self.assertRaisesRegex(SubmissionError, "100 MB"):
                verify_submission(str(out_path), allow_test_only=True, max_package_bytes=10)

    def test_verify_requires_explicit_allow_test_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            out_path = Path(temp_dir) / "test-submission.zip"
            build_submission(str(REPO_ROOT / "fixtures" / "test-logs"), str(out_path), test_only=True)
            with self.assertRaisesRegex(SubmissionError, "requires --allow-test-only"):
                verify_submission(str(out_path), allow_test_only=False)


if __name__ == "__main__":
    unittest.main()
