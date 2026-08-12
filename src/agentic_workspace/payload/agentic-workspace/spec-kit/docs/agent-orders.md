# Portable Agent Orders

An agent order is a bounded operational contract. It is not a decision, a
backlog, or a transcript. It must be executable without access to the chat
where it was prepared.

## Lifecycle

```text
DRAFT → READY → CLAIMED → IN_PROGRESS → EXECUTED → VERIFIED → CLOSED
                         ↕ BLOCKED

Terminal alternatives: CANCELLED, SUPERSEDED, FAILED
```

Retrospective records declare `documentation_mode: retrospective`; they may
represent an already executed, verified, or closed order without pretending
that the normal handoff protocol occurred.

## Files and ownership

`context.json` owns structured intent and constraints. `order.md` is generated.
`result.json` owns actual execution results. `execution-log.md` is append-only.
Handoff files are generated and provider-neutral.

## Closure gate

A mutative order requires a rollback procedure or an explicit justification.
An order cannot close until a structured result exists and a verification ID
is attached. Process exit code 0 or HTTP 200 alone is not behavioral evidence.
The result must satisfy `schemas/order-result.schema.json`; missing required
fields, invalid execution modes, empty executor identities, wrong types, and
unknown properties are rejected before the order changes state. The attached
verification must be a registered `passed` verification with a recorded method
and resolvable evidence.

Claims are leases, not override tokens. `--recover-expired` is required to
replace an expired claim and cannot replace a live claim, even when requested
by another agent.

## Security

Never include passwords, tokens, cookies, authorization headers, `.env`
contents, `.pgpass` contents, or private credential-store values. Reference
credentials only by approved environment-variable name.
