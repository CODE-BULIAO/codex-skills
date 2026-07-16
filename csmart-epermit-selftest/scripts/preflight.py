#!/usr/bin/env python3
"""Run a side-effect-free C-Smart permit self-test preflight."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from discover_permit_targets import discover


def load_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"\'')
    return values


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bot-root", type=Path, default=Path("/root/whatsapp-bot"))
    parser.add_argument("--sender-root", type=Path, default=Path("/home/claw/self-testing-bot-run"))
    parser.add_argument("--target")
    args = parser.parse_args()

    checks: list[dict[str, object]] = []
    try:
        rows = discover(args.bot_root)
        checks.append({"name": "runtime-discovery", "ok": True, "targets": len(rows)})
    except RuntimeError as exc:
        rows = []
        checks.append({"name": "runtime-discovery", "ok": False, "reason": str(exc)})

    allowed = {str(row.get("groupId", "")).strip() for row in rows}
    if args.target:
        checks.append({"name": "target-allowlist", "ok": args.target in allowed, "target": args.target})
    else:
        checks.append({"name": "target-allowlist", "ok": bool(allowed), "reason": "no permit test groups discovered" if not allowed else None})

    env_path = args.sender_root / ".env"
    env = load_env(env_path)
    checks.append({"name": "sender-env", "ok": env_path.is_file(), "path": str(env_path)})
    checks.append({"name": "send-api-secret", "ok": bool(env.get("SEND_API_SECRET"))})

    ready = all(bool(check["ok"]) for check in checks)
    print(json.dumps({"status": "READY" if ready else "BLOCKED", "execute": False, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
