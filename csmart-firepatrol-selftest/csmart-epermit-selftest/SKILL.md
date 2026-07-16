---
name: csmart-epermit-selftest
description: Run and diagnose C-Smart WhatsApp self-tests for E-permit, hot-work permit, paper permit, safety-photo, reminder, shortcode, webhook-state, and permit-record workflows in configured test groups. Use for requests such as "动火许可测试", "纸质 permit 自测", "E-permit webhook 测试", or permit notification and record verification. Do not use for fire-patrol, night-patrol, patrol-point, patrol-range, segmented-summary, or patrol-scheduler tests.
---

# C-Smart E-Permit Self-Test

Run permit workflow self-tests against the active C-Smart bot while routing messages only to permit test groups discovered from runtime configuration.

## Safety Boundary

- Discover targets from the active `/root/whatsapp-bot` runtime; never rely on remembered group IDs.
- Allow only permit groups explicitly listed under runtime test configuration.
- Exclude `BLW`, `BLV_HWP`, `BLW-*`, and `BLV-HWP-*` sites unless the user explicitly changes the boundary.
- Treat the default script mode as preflight only. Require `--execute` before sending text or images.
- Do not delete records, mutate database rows, clean data, or send to a production group.
- Treat queue acceptance as weaker evidence than WhatsApp delivery and persisted state.
- Return `BLOCKED` when routing, configuration, dependencies, images, or evidence interfaces are unavailable.

## Workflow

1. Read `references/permit-workflows.md` before designing or running permit cases.
2. Discover permit test targets:

```bash
python3 scripts/discover_permit_targets.py \
  --bot-root /root/whatsapp-bot \
  --format markdown
```

3. Run preflight and confirm the target, process, required images, allowed prefixes, sender configuration, and production exclusion:

```bash
python3 scripts/preflight.py \
  --bot-root /root/whatsapp-bot \
  --target '<test-group-id>'
```

4. Write a short test design containing case ID, input, expected result, marker, and verification method.
5. Use a unique marker containing site, process, date, and case ID.
6. Run sender commands without `--execute` first and verify the returned `READY` result.
7. Add `--execute` only after the target and payload are confirmed. Execute sequentially when cases share permit state or shortcodes.
8. Verify at least two evidence layers when possible: sender result, WhatsApp response or journal, business log, and records API.
9. Report every case as `PASS`, `FAIL`, or `BLOCKED`; continue later independent cases when a complete matrix is requested.

## Commands

Send text only after the preflight output is correct:

```bash
python3 scripts/send_whatsapp.py \
  --to '<test-group-id>' \
  --message-file /tmp/permit-message.txt

python3 scripts/send_whatsapp.py \
  --to '<test-group-id>' \
  --message-file /tmp/permit-message.txt \
  --execute
```

Send an existing test image with the same two-step pattern:

```bash
python3 scripts/send_image.py \
  --to '<test-group-id>' \
  --image '<existing-test-image>' \
  --caption-file /tmp/permit-caption.txt
```

Query persisted permit records without mutation:

```bash
python3 scripts/query_records.py \
  --group-id '<test-group-id>' \
  --hotwork-apply-id '<permit-id>'
```

## Permit Rules

Use canonical webhook fields:

```text
hotwork_status, hotwork_apply_id, subcontractor, location, floor,
process, date, time_range, number, apply_name, worker_name, approver_name
```

Do not use `permit_status` or `permit_apply_id` as primary fields. Confirm the configured state flow before execution; a common flow is:

```text
submit -> approved -> received_wait_cancel -> wait_cancel_confirm -> cancel_success
```

For paper permits, read `paperPermitRequiredImages` from runtime configuration. Do not infer the required image count.

## Results

- `PASS`: WhatsApp behavior and persisted state satisfy the stated expectation.
- `FAIL`: The path executes but routing, response, validation, persistence, reminder, summary, or record behavior contradicts the expectation.
- `BLOCKED`: A required test group, configuration, interface, dependency, image, or evidence source is unavailable.

Include the exact target group ID, marker, prerequisites, actual response or log, persisted evidence, status totals, and primary defects. Do not hide duplicate timestamps, missing replies, incorrect symbols, production-routing risk, or transport failures.
