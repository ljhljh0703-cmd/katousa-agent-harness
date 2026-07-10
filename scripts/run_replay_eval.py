from __future__ import annotations

import argparse
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_ROOT = os.path.join(REPO_ROOT, "plugins", "calm-trade-growth-harness")
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from calm_trade_growth_harness.replay import run_replay_eval  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fixtures", default=os.path.join(REPO_ROOT, "fixtures"))
    parser.add_argument("--out", default=os.path.join(REPO_ROOT, "dist"))
    args = parser.parse_args()
    report = run_replay_eval(args.fixtures, args.out)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
