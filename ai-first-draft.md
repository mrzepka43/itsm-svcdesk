---
lab3_first_draft:
  source: ai
  tool: "GitHub Copilot (AI assistant in VS Code), 13 October 2026"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
  verdict: refuted
  evidence: {p99_seconds: 0.1138, bucket: [0.1, 0.25], relative_width: 1.318}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: 0.1138, bucket: [0.04, 0.5], relative_width: 4.042}
---
<!-- ai-generated: 85% - the prompt is mine, the answer is GitHub Copilot's verbatim, the verdicts and arithmetic are mine -->

# The assistant's first draft, and two verdicts

## Prompt

I am instrumenting a FastAPI service with a Prometheus histogram http_server_request_duration_seconds (seconds) for GET /kb/search, which calls an upstream knowledge-base index on every request. Give me histogram bucket boundaries (in seconds) and a Prometheus alert rule for this endpoint. I have not measured anything yet.

## Answer

Histogram buckets (seconds): 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10

These are the standard Prometheus default boundaries. They cover everything from 5 ms to 10 s on a roughly logarithmic scale, so they work for most HTTP services without knowing the latency distribution in advance.

Alert rule:

```yaml
groups:
  - name: kb-search
    rules:
      - alert: KbSearchHighErrorRate
        expr: |
          sum(rate(http_server_request_duration_seconds_count{http_route="/kb/search", http_response_status_code=~"5.."}[5m]))
            /
          sum(rate(http_server_request_duration_seconds_count{http_route="/kb/search"}[5m]))
            > 0.05
        for: 10m
        labels:
          severity: page
        annotations:
          summary: "More than 5 % of /kb/search requests fail"
      - alert: KbSearchSlow
        expr: |
          histogram_quantile(0.99, sum by (le) (rate(http_server_request_duration_seconds_bucket{http_route="/kb/search"}[5m]))) > 0.5
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "p99 of /kb/search is above 500 ms"
```

## Verdict on the draft ladder

The measured p99 was 0.1138 seconds. The draft ladder places it in (0.1, 0.25], whose width is 0.15 seconds;
0.15 / 0.1138 = 1.318, or 131.8% of the p99. The bucket is much wider than the 20% resolution limit, so the
draft is refuted. Linear interpolation could report a p99 anywhere across that coarse bucket.

## The draft alert rule

The draft suggested a 5% five-minute error ratio and a 500 ms p99 alert, but neither rule is suitable unchanged:
they are single-window rules, the label severities do not follow this lab's P1/P2/P3 contract, and neither has the
required multiwindow reset behavior. I kept the draft's useful ideas of filtering the search route and detecting
5xx responses, then implemented availability burn alerts with explicit long and short windows and tested edges.

## Verdict on the instructor's flawed ladder

The same p99, 0.1138 seconds, falls in (0.04, 0.5] on the instructor's ladder. Its width is 0.46 seconds;
0.46 / 0.1138 = 4.042, or 404.2% of the p99. The very wide interval cannot resolve the measured slow tail, so
the flawed ladder is refuted.
