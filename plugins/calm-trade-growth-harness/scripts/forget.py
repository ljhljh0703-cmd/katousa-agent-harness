from __future__ import annotations

import argparse
import json
import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from calm_trade_growth_harness.state import forget_event_payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=".calm-trade")
    parser.add_argument("--event-id", required=True)
    parser.add_argument("--source-turn", required=True)
    args = parser.parse_args()
    receipt = forget_event_payload(args.state_dir, event_id=args.event_id, source_turn=args.source_turn)
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
