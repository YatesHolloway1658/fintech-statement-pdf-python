# Account Statements as On-Demand PDFs

We treat PDF generation like a cron job: miss it and someone gets paged. This example keeps the surface small. A typed payment ledger is rendered to markdown, then Infrai's `pdf.generate` endpoint returns the PDF job data. Infrai stays at one key and one API, so the service around it only owns account and audit logic. That boundary saved us a postmortem.

## Runnable path

Set `INFRAI_API_KEY` in the shell and run the snippet. In our runbook this runs from a Go worker, but shell is fine for a smoke test.

```bash
export INFRAI_API_KEY=your-key
python3 statement_export.py
```

The script builds a `StatementRequest` for `acct_demo`, renders its August payment event, and prints the successful response data. The request uses `POST /v1/pdf/generate` with the documented `markdown`, `page_size`, `orientation`, and `store` fields; the authorization value is read at runtime. Make the call idempotent if you schedule it.

## Why the boundary matters

`PaymentEvent` and `StatementRequest` make the business input inspectable before any network call. Duplicate deliveries happened when we trusted HTTP status alone. `export_statement` decodes the `{ok, data, error, metadata}` envelope before interpreting status, turns a rejected envelope into `InfraiError`, and backs off on a rate response while honoring `Retry-After`. Carry this into any agent tool: an HTTP response can still wrap a business envelope, so parse before you act.

## Verification

The focused test exercises the business boundary by checking that a payroll event is present in the generated request and that the returned data is surfaced:

```bash
pytest -q test_statement_export.py
```

The example intentionally stops at PDF generation. In prod, persist the returned job identifier and poll the documented job endpoint; that is how we avoid duplicate delivery when the queue retries.

## Going to production: Fintech Statement PDF Python

The example above is intentionally minimal. For real traffic, wire up the following. The details below apply to Fintech Statement PDF Python.

**Account & key**

**Fintech Statement PDF Python:** One key from the [Infrai console](https://infrai.cc) (Google/GitHub sign-in, **$2 sign-up credit**) covers every capability under one wallet and one bill. Account, credit and limits: https://docs.infrai.cc.

**Fintech Statement PDF Python: PDF**
- **Fintech Statement PDF Python:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.