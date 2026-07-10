from __future__ import annotations

import argparse
import json
import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from calm_trade_growth_harness.state import record_event


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=".calm-trade")
    parser.add_argument("--type", required=True)
    parser.add_argument("--source-turn", required=True)
    parser.add_argument("--content", required=True)
    parser.add_argument("--importance", type=int, default=1)
    parser.add_argument("--confirmation", default="candidate")
    args = parser.parse_args()
    event = record_event(
        args.state_dir,
        event_type=args.type,
        source_turn=args.source_turn,
        content=args.content,
        importance=args.importance,
        confirmation=args.confirmation,
    )
    print(json.dumps(event, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
