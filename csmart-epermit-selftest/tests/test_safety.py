from __future__ import annotations

import sys
from pathlib import Path

import pytest


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import discover_permit_targets  # noqa: E402
import send_image  # noqa: E402
import send_whatsapp  # noqa: E402
import test_group_guard  # noqa: E402


def test_excluded_site_code_patterns() -> None:
    assert discover_permit_targets.is_excluded_site_code("BLW")
    assert discover_permit_targets.is_excluded_site_code("BLW-01")
    assert discover_permit_targets.is_excluded_site_code("BLV_HWP")
    assert discover_permit_targets.is_excluded_site_code("BLV-HWP-02")
    assert not discover_permit_targets.is_excluded_site_code("BLY")


def test_senders_default_to_ready() -> None:
    assert send_whatsapp.execution_status(False) == "READY"
    assert send_image.execution_status(False) == "READY"
    assert send_whatsapp.execution_status(True) == "EXECUTE"


def test_guard_accepts_only_permit_allowlist(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(test_group_guard, "permit_test_groups", lambda _root: {"permit-test@g.us"})
    test_group_guard.require_test_group("permit-test@g.us", Path("/runtime"))
    with pytest.raises(SystemExit, match="non-permit-test"):
        test_group_guard.require_test_group("patrol-test@g.us", Path("/runtime"))
