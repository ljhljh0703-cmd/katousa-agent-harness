from __future__ import annotations

import argparse
import json
import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from calm_trade_growth_harness.state import propose_delta


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--state-dir", default=".calm-trade")
    parser.add_argument("--field", required=True)
    parser.add_argument("--to", required=True)
    parser.add_argument("--basis-event-id", action="append", required=True)
    parser.add_argument("--basis-summary", required=True)
    args = parser.parse_args()
    try:
        new_value = json.loads(args.to)
    except json.JSONDecodeError:
        new_value = args.to
    delta = propose_delta(
        args.state_dir,
        field=args.field,
        new_value=new_value,
        basis_event_ids=args.basis_event_id,
        basis_summary=args.basis_summary,
    )
    print(json.dumps(delta, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
