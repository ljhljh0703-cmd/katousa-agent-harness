from __future__ import annotations

import argparse
import json

from submission_lib import add_common_parser_flags, build_submission


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_parser_flags(parser)
    parser.add_argument("--logs", required=True, help="Path to the raw or fixture log directory")
    parser.add_argument("--out", required=True, help="Output ZIP path")
    parser.add_argument("--test-only", action="store_true", help="Label the package as TEST_ONLY")
    args = parser.parse_args()
    result = build_submission(args.logs, args.out, test_only=args.test_only)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
