<!-- ai-generated: 100% - drafted from the Lab 1 requirements and API contract, then rewritten for a clear service specification -->
# svcdesk Lab 1 specification

## Purpose

The service desk exposes an HTTP API that allows ticket creation, listing, state transitions, SLA inspection and ticket reopen handling for a small internal service-desk workflow.

This Lab 1 specification is written against a contradictory requirements document. The document contains three pairs of requirements that cannot both hold: C1 (the SLA clock for P1), C2 (closed tickets and reopening) and C3 (VIP reporters and the priority matrix). Each conflict has exactly two admissible resolutions, and the checker accepts any of the eight combinations, provided `DECISIONS.md` declares and defends the resolution the running service actually exhibits.

A single prompt can generate code, but it cannot decide which requirement to break and why. That decision is the substantive work of this laboratory and must be defended in writing before the implementation is accepted.

## Scope

This specification covers the first build of `svcdesk` and describes the behaviours required by the Lab 1 contract and the admissible resolution choices for the three contradictory pairs above.

## Conflict model

The three decision pairs are:

### C1 — SLA clock for P1
- admissible values: `wallclock` or `business`
- `wallclock`: P1 SLA runs on the wall-clock target; P2–P4 use business-hours
- `business`: every priority, including P1, uses the business-hours clock

### C2 — closed tickets and reopening
- admissible values: `reopen` or `immutable`
- `reopen`: reopening is allowed from `resolved` and from `closed` within the 7-day window
- `immutable`: reopening is allowed only from `resolved`; closed tickets remain immutable

### C3 — VIP reporters and the priority matrix
- admissible values: `matrix` or `vip`
- `matrix`: priority is computed from impact and urgency only; VIP does not change the result
- `vip`: after matrix calculation, VIP tickets at P3 or P4 are raised to P2

The service implementation must declare one value for each of these decisions in `DECISIONS.md`, and the values must match the behaviour observed on the running service.

## Functional requirements

### 1. Service health
- `GET /health` returns HTTP 200.
- The response body is JSON with at least:
  - `status: "ok"`
  - `service: "svcdesk"`
- Extra fields are allowed.

### 2. Ticket creation
- `POST /tickets` creates a new ticket.
- The request body must be a JSON object.
- Required fields:
  - `title`: non-empty string, 1..200 chars
  - `reporter.name`: non-empty string, 1..100 chars
  - `impact`: integer in 1..3
  - `urgency`: integer in 1..3
- Optional fields:
  - `description`: string up to 4000 chars, defaults to empty string
  - `reporter.email`: string or null, defaults to null
  - `reporter.vip`: boolean, defaults to false
  - `related_to`: string or null, ignored by validation in Lab 1
- Server-owned fields are ignored if provided by the client.
- On validation failure, the response is 400 or 422 with a top-level `error` object.
- On success, the response is HTTP 201 with the full ticket payload.

### 3. Ticket model
A ticket contains:
- `id`: opaque unique non-empty string
- `title`: string
- `description`: string
- `reporter`: object with `name`, `email`, `vip`
- `impact`: integer 1..3
- `urgency`: integer 1..3
- `priority`: computed by the service
- `state`: one of `new`, `acknowledged`, `in_progress`, `resolved`, `closed`
- timestamps for create / acknowledge / resolve / close
- `related_to`: nullable string
- `sla`: object with `ack_due_at` and `resolve_due_at`

### 4. Priority calculation
- Priority is derived from impact and urgency with the provided matrix.
- The client must not specify priority.
- A VIP reporter's ticket is never lower than P2.
- The specific chosen decision for this build is: VIP tickets at P3 or P4 are raised to P2.

### 5. State machine
A ticket follows the transition rules:
- `new` -> `acknowledged` via `POST /tickets/{id}/ack`
- `acknowledged` -> `in_progress` via `POST /tickets/{id}/start`
- `in_progress` -> `resolved` via `POST /tickets/{id}/resolve`
- `resolved` -> `closed` via `POST /tickets/{id}/close`
- `resolved` or `closed` -> `in_progress` via `POST /tickets/{id}/reopen` within the allowed window

Other transitions return `409 Conflict` with a top-level `error` object.

### 6. Reopen rules
- Reopening a resolved ticket is allowed only within 7 days of `resolved_at`.
- Closed tickets are immutable in this build.
- Reopen does not reset the original resolution target.

### 7. Listing and retrieval
- `GET /tickets` returns all tickets, optionally filtered by exact-match:
  - `?state=`
  - `?priority=`
- `GET /tickets/{id}` returns a single ticket or 404 with `error` object.
- Unknown ticket IDs and unknown paths return JSON `404` errors.

### 8. SLA model
- Each ticket has an acknowledgement due instant and a resolution due instant.
- The service computes both based on the creation time and the priority.
- For this build, the accepted decision is:
  - `C1 = wallclock` for P1 tickets
  - other priorities use business-hours logic
- `GET /tickets/{id}/sla` returns:
  - `priority`
  - `ack_due_at`
  - `resolve_due_at`
  - `ack_breached`
  - `resolve_breached`
  - `paused`

### 9. Clock handling
- When the environment variable `SVCDESK_TEST_CLOCK` is enabled, the service accepts an `X-Test-Clock` header.
- The header is used as the request clock for that request only.
- An invalid timestamp returns 400 or 422.
- Without the header, the service uses real UTC time.

### 10. Compose and container contract
- The project ships as a Docker Compose service named `svcdesk`.
- It must build from the repository root and expose port `8080` inside the container.
- `SVCDESK_TEST_CLOCK` must be set to `"1"`.
- No host bind mounts are used.
- The app is intended to run in a containerized environment with a persistent volume for state.

## Non-functional requirements

- The API must return JSON bodies for all successful and error responses.
- All timestamps are RFC 3339 UTC instants with a `Z` suffix where possible.
- The service should be resilient to malformed requests without crashing.
- The implementation should remain small and suitable for the first Lab 1 acceptance checks.

## Decisions for this implementation

This first implementation chooses the following admissible values:
- `C1 = wallclock`
- `C2 = immutable`
- `C3 = vip`

This design is intentionally conservative and easier to reason about in the first build.
