#!/usr/bin/env python3
"""Query C-Smart permit records without mutating data."""

from __future__ import annotations

import argparse
import json
import urllib.error
from urllib.parse import urlencode
from urllib.request import urlopen


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://llm-ai.c-smart.hk/records/today")
    parser.add_argument("--group-id", required=True)
    parser.add_argument("--hotwork-apply-id")
    parser.add_argument("--application-id")
    parser.add_argument("--marker")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    params = {"group_id": args.group_id}
    if args.hotwork_apply_id:
        params["hotwork_apply_id"] = args.hotwork_apply_id
    try:
        with urlopen(args.base_url + "?" + urlencode(params), timeout=args.timeout) as response:
            rows = json.loads(response.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2
    if not isinstance(rows, list):
        print(json.dumps({"status": "BLOCKED", "reason": "records API did not return a list"}, ensure_ascii=False))
        return 2
    if args.application_id:
        rows = [row for row in rows if row.get("application_id") == args.application_id]
    if args.marker:
        rows = [row for row in rows if args.marker in json.dumps(row, ensure_ascii=False)]
    print(json.dumps(rows, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
