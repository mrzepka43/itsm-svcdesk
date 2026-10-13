---
lab3_first_draft:
  source: ai
  tool: "GitHub Copilot (AI assistant in VS Code), 13 October 2026"
  ladder: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
  verdict: TODO
  evidence: {p99_seconds: TODO, bucket: [TODO, TODO], relative_width: TODO}
lab3_flawed_ladder:
  verdict: refuted
  evidence: {p99_seconds: TODO, bucket: [TODO, TODO], relative_width: TODO}
---
<!-- ai-generated: 60% - the prompt is mine, the answer is GitHub Copilot's verbatim, the verdicts and arithmetic are mine -->

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

TODO

## The draft alert rule

TODO

## Verdict on the instructor's flawed ladder

TODO
