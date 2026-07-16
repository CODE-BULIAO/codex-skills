#!/usr/bin/env python3
"""Discover permit self-test targets from a C-Smart bot runtime tree."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any


NODE_SNIPPET = r"""
const botRoot = process.argv[1];
require(`${botRoot}/group_constants.js`);
const {
  PROCESS_NAMES,
  getProcessGroupIds,
  getProcessConfigByGroupId,
} = require(`${botRoot}/site_process_registry.js`);

function isExcludedSiteCode(value) {
  const code = String(value || "").toUpperCase().replaceAll("-", "_");
  return code === "BLW" || code.startsWith("BLW_") ||
    code === "BLV_HWP" || code.startsWith("BLV_HWP_");
}

const rows = [];
const processNames = [
  PROCESS_NAMES.HOTWORK,
  PROCESS_NAMES.EPERMIT,
  PROCESS_NAMES.PAPER_PERMIT,
].filter(Boolean);

for (const processName of processNames) {
  for (const gid of getProcessGroupIds(processName, {includeTest: true})) {
    const cfg = getProcessConfigByGroupId(processName, gid);
    if (!cfg || isExcludedSiteCode(cfg.siteCode)) continue;
    const pc = cfg.processConfig || {};
    const testGroups = (pc.groups && pc.groups.test) || [];
    if (!testGroups.includes(gid)) continue;
    rows.push({
      siteCode: cfg.siteCode,
      siteName: cfg.siteName,
      groupId: gid,
      processName,
      permitPrefixes: pc.permitPrefixes || [],
      permitType: pc.permitType || "",
      permitTitle: pc.permitTitle || "",
      paperPermit: Boolean(pc.paperPermit),
      requiredImages: Number(pc.paperPermitRequiredImages || 0),
      requireFloor: Boolean(pc.paperPermitRequireFloor),
      allowedProcessPrefixes: pc.paperPermitAllowedProcessPrefixes || [],
      includeLocation: pc.includeLocation !== false,
      includeFloor: Boolean(pc.includeFloor),
      includeProcess: pc.includeProcess !== false,
      route: pc.route || "",
    });
  }
}
console.log(JSON.stringify(rows, null, 2));
"""


def is_excluded_site_code(value: str) -> bool:
    code = value.upper().replace("-", "_")
    return code == "BLW" or code.startswith("BLW_") or code == "BLV_HWP" or code.startswith("BLV_HWP_")


def discover(bot_root: Path, timeout: int = 30) -> list[dict[str, Any]]:
    required = (bot_root / "group_constants.js", bot_root / "site_process_registry.js")
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise RuntimeError("missing runtime files: " + ", ".join(missing))

    try:
        result = subprocess.run(
            ["node", "-e", NODE_SNIPPET, str(bot_root)],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("node executable is unavailable") from exc
    except subprocess.TimeoutExpired as exc:
        raise RuntimeError(f"permit target discovery timed out after {timeout}s") from exc

    if result.returncode != 0:
        raise RuntimeError(f"permit target discovery failed: {result.stderr.strip()}")
    try:
        rows = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("permit target discovery returned invalid JSON") from exc
    if not isinstance(rows, list):
        raise RuntimeError("permit target discovery did not return a list")
    return [row for row in rows if isinstance(row, dict)]


def print_markdown(rows: list[dict[str, Any]]) -> None:
    print("| Site | Group | Process | Prefixes | Type | Paper | Required Images | Notes |")
    print("|---|---|---|---|---|---|---:|---|")
    for row in rows:
        prefixes = ", ".join(row.get("permitPrefixes", [])) or "-"
        notes = []
        if row.get("allowedProcessPrefixes"):
            notes.append("工序: " + " / ".join(row["allowedProcessPrefixes"]))
        if row.get("requireFloor"):
            notes.append("floor required")
        print(
            "| {site} | {group} | {process} | {prefixes} | {permit_type} | {paper} | {images} | {notes} |".format(
                site=row.get("siteCode", ""),
                group=row.get("groupId", ""),
                process=row.get("processName", ""),
                prefixes=prefixes,
                permit_type=row.get("permitType", ""),
                paper="yes" if row.get("paperPermit") else "no",
                images=row.get("requiredImages", 0),
                notes="; ".join(notes),
            )
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bot-root", type=Path, default=Path("/root/whatsapp-bot"))
    parser.add_argument("--format", choices=("json", "markdown"), default="json")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    try:
        rows = discover(args.bot_root, args.timeout)
    except RuntimeError as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2

    if args.format == "json":
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        print_markdown(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
