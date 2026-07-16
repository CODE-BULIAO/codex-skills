# Permit Test Workflows

## Runtime Sources

- Bot root: `/root/whatsapp-bot`
- Webhook: `POST http://127.0.0.1:3333/webhook/fire-paper`
- Text and image sender root: `/home/claw/self-testing-bot-run`
- Records API: `http://llm-ai.c-smart.hk/records/today`
- WhatsApp journal: `journalctl --user -u self-testing-bot`
- Business log: `/root/whatsapp-bot/logs/<group-id>/<YYYY-MM-DD>.log`

Always rediscover the target and runtime values before use.

## Webhook States

Capture the HTTP response, WhatsApp notification, record ID, group ID, permit ID, status, shortcode, effective or leave time, and source fields.

Use these canonical fields unless runtime code proves otherwise:

```text
hotwork_status, hotwork_apply_id, subcontractor, location, floor,
process, date, time_range, number, apply_name, worker_name, approver_name
```

Verify each requested state routes only to the selected test group before posting it.

## Paper Permits

Capture the message type, saved image path when applicable, bot response, shortcode, status, group ID, and the configured paper-source representation.

Read these values from runtime configuration:

- `paperPermitRequiredImages`
- `paperPermitRequireFloor`
- `paperPermitAllowedProcessPrefixes`
- permit title and route

Do not infer image requirements from previous sites or tests.

## Safety Photos

Capture the response, shortcode, period, role, history fields, summary symbols, and duplicate timestamps. Verify both the immediate response and the persisted history.

## Reminders and Summaries

Create controlled pending or active test records through supported interfaces before sending a manual query. Inspect scheduler expressions and historical success or failure logs separately.

A cron expression is configuration evidence. A historical success or failure log is runtime evidence. Do not mark a scheduler case `PASS` from configuration alone.

## Evidence Standard

Prefer at least two independent layers:

1. Sender or webhook result.
2. WhatsApp response or self-testing-bot journal.
3. C-Smart business log.
4. Records API result.

Queue acceptance alone does not prove delivery or persistence.
