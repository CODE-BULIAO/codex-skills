#!/usr/bin/env python3
"""Send text through the local self-testing bot after a permit-only safety check."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from test_group_guard import require_test_group


DEFAULT_ROOT = Path("/home/claw/self-testing-bot-run")
DEFAULT_HEALTH_URL = "http://127.0.0.1:13080/health"
DEFAULT_SEND_URL = "http://127.0.0.1:13081/send"


def load_env(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RuntimeError(f"env file not found: {path}")
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"\'')
    return values


def request_json(
    url: str,
    payload: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 15,
) -> tuple[int, dict[str, Any]]:
    data = None
    method = "GET"
    request_headers = headers or {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode()
        method = "POST"
        request_headers = {"Content-Type": "application/json", **request_headers}
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode()
            return response.status, json.loads(body or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode()
        try:
            parsed = json.loads(body or "{}")
        except json.JSONDecodeError:
            parsed = {"raw": body}
        return exc.code, parsed


def check_health(url: str, timeout: int) -> dict[str, Any]:
    status, body = request_json(url, timeout=timeout)
    if status != 200:
        raise RuntimeError(f"health HTTP {status}: {body}")
    if body.get("status") != "READY" or body.get("isConnected") is not True:
        raise RuntimeError(f"self-testing bot not ready: {body}")
    return body


def recent_journal(lines: int) -> str:
    result = subprocess.run(
        ["journalctl", "--user", "-u", "self-testing-bot", "-n", str(lines), "--no-pager"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return result.stdout


def execution_status(execute: bool) -> str:
    return "EXECUTE" if execute else "READY"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--bot-root", type=Path, default=Path("/root/whatsapp-bot"))
    parser.add_argument("--env", type=Path)
    parser.add_argument("--health-url", default=DEFAULT_HEALTH_URL)
    parser.add_argument("--send-url", default=DEFAULT_SEND_URL)
    parser.add_argument("--to", required=True)
    message_group = parser.add_mutually_exclusive_group(required=True)
    message_group.add_argument("--message")
    message_group.add_argument("--message-file", type=Path)
    parser.add_argument("--execute", action="store_true", help="perform the send after preflight")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--retry-delay", type=float, default=2.0)
    parser.add_argument("--skip-health", action="store_true")
    parser.add_argument("--expect-log", default="")
    parser.add_argument("--expect-wait", type=float, default=6.0)
    parser.add_argument("--journal-lines", type=int, default=120)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    env_path = args.env or args.root / ".env"
    try:
        env = load_env(env_path)
    except RuntimeError as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 2

    secret = env.get("SEND_API_SECRET") or os.getenv("SEND_API_SECRET", "")
    if not secret:
        print(json.dumps({"status": "BLOCKED", "reason": "SEND_API_SECRET is missing"}, ensure_ascii=False))
        return 2

    blocked = {item.strip() for item in env.get("BLOCKED_SEND_CHAT_IDS", "").split(",") if item.strip()}
    if args.to in blocked:
        print(json.dumps({"status": "BLOCKED", "reason": "target is explicitly blocked", "to": args.to}, ensure_ascii=False))
        return 2

    try:
        require_test_group(args.to, args.bot_root)
    except (RuntimeError, SystemExit) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc), "to": args.to}, ensure_ascii=False))
        return 2

    message = args.message if args.message is not None else args.message_file.read_text(encoding="utf-8")
    if not message.strip():
        print(json.dumps({"status": "BLOCKED", "reason": "message is empty"}, ensure_ascii=False))
        return 2

    if not args.execute:
        print(json.dumps({"status": "READY", "execute": False, "to": args.to, "message_length": len(message)}, ensure_ascii=False))
        return 0

    if not args.skip_health:
        try:
            health = check_health(args.health_url, args.timeout)
            print(json.dumps({"phase": "health", "ok": True, "status": health.get("status")}, ensure_ascii=False))
        except Exception as exc:
            print(json.dumps({"status": "BLOCKED", "phase": "health", "reason": str(exc)}, ensure_ascii=False))
            return 3

    last_status = 0
    last_body: dict[str, Any] = {}
    for attempt in range(1, max(args.retries, 1) + 1):
        try:
            last_status, last_body = request_json(
                args.send_url,
                payload={"to": args.to, "message": message},
                headers={"x-send-api-secret": secret},
                timeout=args.timeout,
            )
        except Exception as exc:
            last_status, last_body = 0, {"ok": False, "error": str(exc)}
        print(json.dumps({"phase": "send", "attempt": attempt, "http": last_status, "body": last_body}, ensure_ascii=False))
        if last_status == 200 and last_body.get("ok") is True:
            break
        if last_status in (400, 401, 403):
            return 4
        time.sleep(args.retry_delay * attempt)
    else:
        return 5

    if args.expect_log:
        time.sleep(args.expect_wait)
        logs = recent_journal(args.journal_lines)
        matched = re.search(args.expect_log, logs, re.MULTILINE) is not None and args.to in logs
        print(json.dumps({"phase": "expect-log", "ok": matched, "pattern": args.expect_log, "to": args.to}, ensure_ascii=False))
        if not matched:
            return 6
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
