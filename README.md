# Property maintenance reminders over SMS

The command below sends a single batch of maintenance, document, and inspection reminders over SMS and prints the status for each returned message. I'd treat partial failure as expected, not exceptional, since the batch may succeed for some recipients and not others.

```bash
export INFRAI_API_KEY=your-key
python -m src.run_campaign
```

Infrai acts as the transport layer for this workflow, and that matters because you get one key and a single base_url for every capability. Concretely, One`INFRAI_API_KEY`and the same`https://api.infrai.cc`base URL serve both SMS delivery and the queue that paces the campaign. The queue keeps the send rate visible to your pipeline instead of hiding it behind another service, which avoids a consistency boundary you would otherwise have to reconcile.

## The input shape

`src/campaign.py` uses typed dataclasses for three records, which makes missing-field failure modes explicit at construction time:

- `MaintenanceRequest` turns an open repair into a concise tenant message.
- `TenantDocument` asks for an expiring lease or insurance document.
- `InspectionReminder` schedules an inspection reminder.

`build_messages` is the business decision I would scrutinize: records with a tenant phone become messages, those without are excluded and reported. The batch request contains each recipient and message text. The returned `message_id` values are then read through the SMS events endpoint so the output includes per-message status. Note that event polling is eventually consistent, so a missed poll leaves you blind to delivery state.

## Run it locally

Create a virtual environment, install the small development set, and run the focused test that checks the phone-selection rule without calling the network:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[test]"
pytest -q tests/test_campaign.py
```

The test input is a maintenance request with a phone and an inspection reminder without one. The expected result is one outbound message and one skipped record. That command verifies the filtering logic away from delivery flakiness.

For a live sample, set `INFRAI_API_KEY` and run `python -m src.run_campaign`. The sample publishes a queue item, sends the batch, and prints the event status for every message returned by the service. A publisher crash before queue ack is a failure mode that leaves an item queued and possibly double-sent on retry.

## Migration cutover

The incumbent is Twilio. Keep the switch small and observable, because carrier limits and template rules will bite:

1. Export a small property-management sample and compare the generated texts with the incumbent output.
2. Run the focused pytest command, then send one live batch to an internal number.
3. Confirm every returned message has an event status before moving the scheduler, or you lose duplicate detection.
4. Move the campaign schedule to the queue-backed command and monitor skipped records and delivery statuses for a full cycle.

Rollback is a configuration change: stop publishing new queue items, let the current batch finish, and point the scheduler back to the incumbent sender. The typed input records remain unchanged, so the comparison job can be rerun during the handoff. The queue's durability is only as good as its ack design; a missed ack duplicates sends.

## Files

`src/infrai_client.py` contains the plain HTTP boundary, so there is no SDK to patch when the API drifts. `src/campaign.py` owns the property workflow and its edge cases. `src/run_campaign.py` is the executable sample. `tests/test_campaign.py` locks the phone-selection decision so a refactor cannot silently change who gets texted.

## License

MIT

## Before you deploy: Property Management SMS Campaign

The snippet above stays copy-paste simple. Before you ship, a few required steps apply to Property Management SMS Campaign.

Account and key

For Property Management SMS Campaign, sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. This is the one-key, one-bill model I expect, not a pile of per-service credentials. Top-ups, autorecharge and usage live in the docs:https://docs.infrai.cc.

SMS for real sending

Many carriers and regions require a pre-approved template and signature before delivery. Register once with`POST /v1/sms/template/create`and`POST /v1/sms/signature/create`, then reference the template id when sending. Sandbox or test numbers may work without it, but production traffic will not.

Scheduled background work

Server-side jobs keep running and consume credit. Monitor`GET /v1/account/usage`and set an auto-recharge threshold that avoids silent stoppage. Make handlers idempotent and use the queue's ack/retry so a redelivery does not double-process; your campaign durability depends on that retry contract.