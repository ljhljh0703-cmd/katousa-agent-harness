from __future__ import annotations

import argparse
import json
import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from calm_trade_growth_harness.state import apply_delta, reject_delta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=".calm-trade")
    parser.add_argument("--delta-id", required=True)
    parser.add_argument("--source-turn", required=True)
    parser.add_argument("--confirm", action="store_true")
    parser.add_argument("--confirmation-evidence")
    parser.add_argument("--reject-reason")
    args = parser.parse_args()
    if args.reject_reason:
        result = reject_delta(
            args.state_dir,
            delta_id=args.delta_id,
            reason=args.reject_reason,
            source_turn=args.source_turn,
        )
    else:
        result = apply_delta(
            args.state_dir,
            delta_id=args.delta_id,
            source_turn=args.source_turn,
            user_confirmation=args.confirm,
            confirmation_evidence=args.confirmation_evidence,
        )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
