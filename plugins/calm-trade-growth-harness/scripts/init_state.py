from __future__ import annotations

import argparse
import json
import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from calm_trade_growth_harness.contracts import read_json
from calm_trade_growth_harness.state import init_state


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=".calm-trade")
    parser.add_argument("--profile", help="Optional profile fixture JSON path")
    args = parser.parse_args()
    profile = read_json(args.profile) if args.profile else None
    result = init_state(args.state_dir, profile)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
