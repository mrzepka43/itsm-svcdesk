---
lab4_postmortem:
  ticket: "3ba75e92-1b55-483b-a69e-6097c02b182c"
  detecting_alert: ShopCheckoutSlow
  onset: 2026-10-12T05:01:00Z
  detection: 2026-10-12T05:06:19Z
  acknowledgement: 2026-10-12T05:06:56Z
  recovery: 2026-10-12T05:08:19Z
  mttd_seconds: 319
  mtta_seconds: 37
  mttr_seconds: 439
  identified_flags: [adFailure, intlShippingSlowdown, emailMemoryLeak]
---
<!-- ai-generated: 60% - Copilot assembled this postmortem from the supplied recording and checked metric values -->

# Postmortem: Checkout latency and related service symptoms on 12 October

## Date

The recorded incident began on 12 October 2026. This postmortem was prepared on 30 October 2026 from the supplied recording.

## Authors

Written by the on-call engineer for the `mrzepka43` course account, using the supplied incident ticket and Prometheus snapshot.

## Status

Service recovery is recorded; the incident ticket remains acknowledged rather than resolved, and follow-up actions are proposed below.

## Summary

Checkout latency rose after the recorded fault onset at 05:01:00Z. The detecting alert fired at 05:06:19Z and its firing run ended at 05:08:19Z.

## Impact

At 05:04:30Z, the 5-minute p95 for the checkout `PlaceOrder` server span was 5,500 ms; the same query returned 48 ms at 04:56:00Z. Shipping's `POST /ship-order` p95 rose from 1.9 ms to 5,500 ms, while email's `POST /send_order_confirmation` p95 rose from 7.7 ms to 110 ms. The Ad service's `GetAds` server errors rose from no error series at baseline to 0.0108 errors/s. The latency query was `histogram_quantile(0.95, sum by (le) (rate(traces_span_metrics_duration_milliseconds_bucket{service_name="checkout",span_name="oteldemo.CheckoutService/PlaceOrder",span_kind="SPAN_KIND_SERVER"}[5m])))`; the companion queries select `shipping` with `span_name="POST /ship-order"` and `email` with `span_name="POST /send_order_confirmation"` in the same histogram, and measure Ad errors with `sum(rate(traces_span_metrics_calls_total{service_name="ad",span_name="oteldemo.AdService/GetAds",span_kind="SPAN_KIND_SERVER",status_code="STATUS_CODE_ERROR"}[5m]))`. These values describe span observations, not a count of unique affected customers.

## Root Causes

The recorded symptoms support three fault-pool candidates: ad server errors, slow checkout shipping orders, and increased email confirmation latency. The corresponding pool flags are `adFailure`, `intlShippingSlowdown`, and `emailMemoryLeak`; the recording's sealed fault is not locally readable, so these are symptom-based identifications rather than a claim that the flag state was directly observed.

## Trigger

The snapshot records `seeded_fault_active` beginning at 05:01:00Z. The recorded data does not expose a per-flag activation log or the exact feature-flag variants.

## Resolution

The detecting alert's firing run ended at 05:08:19Z, which is the recorded recovery time for this alert. The supplied snapshot does not identify the individual flag-off timestamps or their order, so this report does not assign an unverified rollback sequence.

## Detection

`ShopCheckoutSlow` was the earliest qualifying alert, starting at 05:06:19Z, 319 seconds after onset. The ticket was acknowledged 37 seconds after detection. Without the page, the on-call would have needed to notice the checkout latency in the dashboards or traces.

## Action Items

| Action Item | Type | Owner | Bug |
|---|---|---|---|
| Add a checkout latency regression check that covers slow downstream shipping calls. | prevent | Service team | LAB4-01 |
| Add a runbook step to compare ad errors, shipping latency, and email latency when checkout slows. | process | On-call team | LAB4-02 |

## Lessons Learned

### What went well

The P1 ticket was acknowledged after detection, and the snapshot preserves enough telemetry to reconstruct the alert and compare incident symptoms with baseline values.

### What went wrong

The recorded investigator made unsupported causal claims from malformed PromQL and counter values, and it did not identify a verified root cause in its final response.

### Where we got lucky

The checkout latency signal was still measurable in the snapshot, and the alert run resolved before the recording ended, allowing the incident clocks to be recomputed.

## Timeline

- 04:56:00Z — baseline comparison: checkout `PlaceOrder` p95 was 48 ms.
- 05:01:00Z — onset: first `seeded_fault_active` sample.
- 05:04:30Z — checkout `PlaceOrder` p95 measured 5,500 ms; this is also the time used for the ledger predictions.
- 05:06:19Z — `ShopCheckoutSlow` began firing.
- 05:06:56Z — the P1 ticket was acknowledged.
- 05:08:19Z — the detecting alert's firing run ended; recorded recovery.

## Supporting information

The ticket is `incident/ticket.json`; the source time series are in `incident/tsdb-snapshot.tar.gz`; the recorded investigator's exact statements are in `ai-rca/transcript.md`. The four instants and three durations above are copied from `itsmlab incident 4`. The scorecard's predictions use the recording at 05:04:30Z and are separately re-evaluated by the checker.

## Problem record

- Incident record: Ticket 3ba75e92-1b55-483b-a69e-6097c02b182c remains acknowledged in the supplied ticket; no resolved timestamp is recorded.
- Root cause: The symptom evidence points to ad failure, shipping slowdown, and email latency, but the sealed fault cannot be opened locally.
- Known error: The recorded investigator used invalid grouping syntax and inferred causes from cumulative call counts without validating the relevant measurements.
- Workaround: The recording's overall fault ended and the detecting alert recovered; exact per-flag rollback actions are not present in the supplied artifacts.
