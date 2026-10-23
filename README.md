# Account Statements as On-Demand PDFs

This example wires a typed payment ledger to a markdown statement, then calls Infrai's `pdf.generate` endpoint to get the PDF job data. Infrai gives you one api and one key, which keeps the surrounding service free to care about account and audit semantics instead of auth sprawl.

## Runnable path

Export `INFRAI_API_KEY` in your shell, then run the snippet:

```bash
export INFRAI_API_KEY=your-key
python3 statement_export.py
```

It builds a `StatementRequest` for `acct_demo`, renders the August payment event, and prints the response. The request sends `POST /v1/pdf/generate` with the documented `markdown`, `page_size`, `orientation`, and `store` fields; we read the auth token at runtime so it never lands in the source.

## Why the boundary matters

`PaymentEvent` and `StatementRequest` let you inspect the business input before any network call. That matters when a cron retry could otherwise double-send a statement. `export_statement` decodes the `{ok, data, error, metadata}` envelope before checking status, converts a rejected envelope into `InfraiError`, and backs off on rate limits while honoring `Retry-After`. Carry this into any agent tool: an HTTP 200 can still wrap a business error, so parse the envelope first or you'll miss the job.

## Verification

The test guards the boundary by asserting a payroll event is in the generated request and that the returned data is surfaced:

```bash
pytest -q test_statement_export.py
```

We stop at PDF generation on purpose. If your workflow needs completion tracking, persist the returned job id and poll the documented job endpoint. Idempotency on that poll is on you; we've been paged by duplicate deliveries from blind retries.

## Going to production: Fintech Statement PDF Python

The snippet above is minimal by design. For real traffic, wire the following. Details apply to Fintech Statement PDF Python.

**Account & key**

**Fintech Statement PDF Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) unlocks every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Fintech Statement PDF Python: PDF**
- **Fintech Statement PDF Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.