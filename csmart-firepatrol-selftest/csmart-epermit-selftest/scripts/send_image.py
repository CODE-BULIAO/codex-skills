#!/usr/bin/env python3
"""Send an existing image after a permit-only test-group safety check."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from test_group_guard import require_test_group


DEFAULT_ROOT = Path("/home/claw/self-testing-bot-run")


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


def post_json(url: str, secret: str, payload: dict[str, str], timeout: int) -> tuple[int, str]:
    request = Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json", "x-send-api-secret": secret},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read().decode(errors="replace")
    except HTTPError as exc:
        return exc.code, exc.read().decode(errors="replace")
    except URLError as exc:
        raise RuntimeError(f"failed to call {url}: {exc}") from exc


def execution_status(execute: bool) -> str:
    return "EXECUTE" if execute else "READY"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--bot-root", type=Path, default=Path("/root/whatsapp-bot"))
    parser.add_argument("--env", type=Path)
    parser.add_argument("--url")
    parser.add_argument("--to", required=True)
    parser.add_argument("--image", type=Path, required=True)
    parser.add_argument("--image-name")
    caption_group = parser.add_mutually_exclusive_group(required=True)
    caption_group.add_argument("--caption")
    caption_group.add_argument("--caption-file", type=Path)
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--execute", action="store_true", help="perform the send after preflight")
    args = parser.parse_args()

    image = args.image.expanduser().resolve()
    if not image.is_file():
        print(json.dumps({"status": "BLOCKED", "reason": f"image not found: {image}"}, ensure_ascii=False))
        return 2
    if not args.to.endswith("@g.us"):
        print(json.dumps({"status": "BLOCKED", "reason": "target must end in @g.us"}, ensure_ascii=False))
        return 2
    try:
        require_test_group(args.to, args.bot_root)
    except (RuntimeError, SystemExit) as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc), "to": args.to}, ensure_ascii=False))
        return 2

    caption = args.caption if args.caption is not None else args.caption_file.read_text(encoding="utf-8")
    if not caption.strip():
        print(json.dumps({"status": "BLOCKED", "reason": "caption is empty"}, ensure_ascii=False))
        return 2

    env_path = args.env or args.root / ".env"
    env = load_env(env_path)
    secret = env.get("SEND_API_SECRET", "")
    if not secret:
        print(json.dumps({"status": "BLOCKED", "reason": "SEND_API_SECRET is missing"}, ensure_ascii=False))
        return 2

    port = env.get("SEND_API_PORT", "13081")
    url = args.url or f"http://127.0.0.1:{port}/send-image"
    payload = {
        "to": args.to,
        "imagePath": str(image),
        "imageName": args.image_name or image.name,
        "caption": caption,
    }
    if not args.execute:
        print(json.dumps({"status": "READY", "execute": False, "url": url, "payload": payload}, ensure_ascii=False, indent=2))
        return 0

    try:
        status, body = post_json(url, secret, payload, args.timeout)
    except RuntimeError as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc)}, ensure_ascii=False))
        return 3
    print(json.dumps({"status": status, "response": body}, ensure_ascii=False, indent=2))
    return 0 if 200 <= status < 300 else 1


if __name__ == "__main__":
    raise SystemExit(main())
