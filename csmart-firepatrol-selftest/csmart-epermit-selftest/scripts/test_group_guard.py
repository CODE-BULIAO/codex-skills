"""Resolve and enforce the runtime permit test-group allowlist."""

from __future__ import annotations

from pathlib import Path

from discover_permit_targets import discover


def permit_test_groups(bot_root: Path = Path("/root/whatsapp-bot")) -> set[str]:
    return {
        str(row.get("groupId", "")).strip()
        for row in discover(bot_root)
        if str(row.get("groupId", "")).strip().endswith("@g.us")
    }


def require_test_group(target: str, bot_root: Path = Path("/root/whatsapp-bot")) -> None:
    allowed = permit_test_groups(bot_root)
    if target not in allowed:
        raise SystemExit(f"Refusing unlisted/non-permit-test target: {target}")
