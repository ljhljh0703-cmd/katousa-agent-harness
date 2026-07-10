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

from calm_trade_growth_harness.replay import run_replay_eval  # noqa: E402


class ReplayEvalTests(unittest.TestCase):
    def test_replay_eval_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as out_dir_one, tempfile.TemporaryDirectory() as out_dir_two:
            report_one = run_replay_eval(os.path.join(REPO_ROOT, "fixtures"), out_dir_one)
            report_two = run_replay_eval(os.path.join(REPO_ROOT, "fixtures"), out_dir_two)

            self.assertEqual(report_one["profiles"], report_two["profiles"])
            self.assertEqual(report_one["cases"], report_two["cases"])
            self.assertEqual(report_one["total_runs"], report_two["total_runs"])
            self.assertEqual(report_one["pass_count"], report_two["pass_count"])
            self.assertEqual(report_one["fail_count"], report_two["fail_count"])
            self.assertTrue(report_one["all_invariants_stable"])

            with open(os.path.join(out_dir_one, "replay-metrics.json"), "r", encoding="utf-8") as handle:
                metrics = json.load(handle)
            self.assertTrue(metrics["process_metrics_only"])

    def test_replay_outputs_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as out_dir:
            run_replay_eval(os.path.join(REPO_ROOT, "fixtures"), out_dir)
            for name in ["replay-report.md", "replay-metrics.json", "replay-trace.jsonl"]:
                self.assertTrue(os.path.exists(os.path.join(out_dir, name)))


if __name__ == "__main__":
    unittest.main()
