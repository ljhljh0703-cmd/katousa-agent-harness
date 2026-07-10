from __future__ import annotations

import argparse
import json

from submission_lib import add_common_parser_flags, verify_submission


def main() -> int:
    parser = argparse.ArgumentParser()
    add_common_parser_flags(parser)
    parser.add_argument("archive_path")
    parser.add_argument("--allow-test-only", action="store_true")
    args = parser.parse_args()
    result = verify_submission(args.archive_path, allow_test_only=args.allow_test_only)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
