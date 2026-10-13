---
lab3_slo:
  service: svcdesk
  route: /kb/search
  window: 30d
  slis:
    availability:
      objective: 0.99
      good: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search", http_response_status_code!~"5.."}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.01, minutes: 432}
    latency:
      objective: 0.95
      threshold_seconds: 0.12
      good: 'sum(rate(http_server_request_duration_seconds_bucket{job="svcdesk", http_route="/kb/search", le="0.12"}[5m]))'
      valid: 'sum(rate(http_server_request_duration_seconds_count{job="svcdesk", http_route="/kb/search"}[5m]))'
      error_budget: {fraction: 0.05, minutes: 2160}
  alerts:
    - {alert: KbSearchErrorsBurnFast, sli: availability, burn_rate: 14.4, long_window: 1h, short_window: 5m}
    - {alert: KbSearchErrorsBurnSlow, sli: availability, burn_rate: 6, long_window: 6h, short_window: 30m}
---
<!-- ai-generated: 85% - drafted with GitHub Copilot from measured latency and the Lab 3 SLO rules, then checked against the Prometheus queries -->

# SLO for `GET /kb/search`

## Availability

The availability objective is 99% over 30 days. Good requests are any `/kb/search` responses that are not 5xx;
all `/kb/search` requests are valid. The error budget is 1% of valid requests, or 432 minutes of a 30-day window
at a steady request rate. This is a dependency-backed endpoint, so transient `kb-index` failures count against the
budget even though svcdesk cannot repair the index itself. The objective leaves room for those upstream failures
while requiring sustained reliability from the service.

## Latency

The latency objective is 95% of valid searches at or below 120 ms. That threshold is a finite histogram boundary,
so the good-request query counts observations directly rather than interpolating a quantile. The first open-loop
measurement gave p50 18.8 ms and p99 113.8 ms, with a pronounced slow tail (p99.9 132.8 ms); 120 ms is just above
that measured p99 and below the tail. A 95% objective is intentionally less strict than availability because
individual slow-mode requests are expected from the seeded upstream. Its 5% error budget is 2,160 minutes over
30 days.

## Alerts

| alert | SLI | burn rate | long / short window | budget spent when it fires | severity: page or chat |
|---|---|---:|---|---|---|
| KbSearchErrorsBurnFast | availability | 14.4 | 1h / 5m | 2% in the long window | P1 page |
| KbSearchErrorsBurnSlow | availability | 6 | 6h / 30m | 5% in the long window | P2 chat |

The P1 alert pages when the error budget is disappearing at a pace that would consume it in about 2.1 days; the
short window prevents paging on an old incident that has already recovered. The P2 alert catches a slower but
sustained burn over a longer window and goes to chat, giving the team time to investigate without waking someone
for an issue whose impact is accumulating more gradually.

## Buckets

The initial measured p99 was 113.8 ms. The final ladder narrows the region around it to 10 ms buckets; the bucket
holding this measurement is (0.11, 0.12], about 8.8% of the p99. The surrounding boundaries at 0.10 and 0.13
resolve at least a ±10% band around the measured value, while the wider lower and upper ranges retain useful
coverage without exceeding the 30-boundary limit.
