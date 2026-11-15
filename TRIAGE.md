---
lab5_triage:
  image: ghcr.io/mrzepka43/itsm-svcdesk@sha256:8542f516492f471dc54d08e4a83101cd5b7992127d7f3e48f81fffcb232778d9
  sarif_receipt: 439
---
<!-- ai-generated: 100% - Copilot recorded the observed first-run findings and the corresponding changes -->
# Triage

The initial image scan on main reported the following fixable HIGH findings. The updated image passed the same
Trivy image gate locally and on the subsequent main run. The Semgrep rows cover findings on this repository in
the SARIF receipted by issue 439. The two accepted risks are due for review on 2026-11-15.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| trivy | CVE-2026-76844 | fix | Trivy reported zlib1g; the Dockerfile upgrades it to Debian's fixed package. |
| trivy | CVE-2026-85091 | fix | Trivy reported zlib1g; the Dockerfile upgrades it to Debian's fixed package. |
| trivy | CVE-2026-114613 | fix | Removed pip and its vendored msgpack from the runtime image after installing dependencies. |
| trivy | GHSA-6v7p-g79w-8964 | fix | Removed pip and its vendored msgpack from the runtime image after installing dependencies. |
| trivy | CVE-2025-47273 | fix | Removed pip and its vendored setuptools from the runtime image after installing dependencies. |
| trivy | CVE-2024-47874 | fix | Upgraded FastAPI and pinned Starlette 1.10.0 in requirements.txt, beyond the reported fixed version. |
| trivy | CVE-2026-48818 | fix | Upgraded FastAPI and pinned Starlette 1.10.0 in requirements.txt, beyond the reported fixed version. |
| trivy | CVE-2026-54283 | fix | Upgraded FastAPI and pinned Starlette 1.10.0 in requirements.txt, beyond the reported fixed version. |
| trivy | CVE-2026-97687 | fix | Removed pip and its vendored urllib3 from the runtime image after installing dependencies. |
| trivy | CVE-2026-97689 | fix | Removed pip and its vendored urllib3 from the runtime image after installing dependencies. |
| semgrep | dockerfile.security.missing-user.missing-user | accept | Dockerfile runs the service as root; preserving access to the existing data volume. Review 2026-11-15. |
| semgrep | python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected | accept | lab4/agent/prom_mcp.py uses a configured Prometheus URL and follows redirects; keep Lab 4 unchanged. Review 2026-11-15. |

## Bake-off

The set has nine labelled defects. Trivy found three (TP 3, FP 0, FN 6; precision 1.0000, recall 0.3333,
F1 0.5000). Gitleaks, Grype and OSV-Scanner each found two with no false positives (TP 2, FP 0, FN 7;
precision 1.0000, recall 0.2222, F1 0.3636). Semgrep found four but also reported two false positives
(TP 4, FP 2, FN 5; precision 0.6667, recall 0.4444, F1 0.5333).

I would retain Trivy and gitleaks as gates because their findings in this set had no false positives and cover
different kinds of risk. Grype and OSV-Scanner also found the two labelled dependency defects; keeping their
reports provides additional evidence without assuming this small sample proves they always agree with Trivy.
Semgrep found code defects the others missed, but its two false positives make it a useful review signal rather
than an automatic blocking gate on this evidence alone. Different tools target different classes, so comparing
their overall recall against all nine defects is not a comparison of like-for-like coverage.

The path-traversal, access-control and one secret defect were missed by all five under the published matching
rule. This surprised me: neither a clean dependency scan nor a secrets gate guarantees that application logic
and every credential have been checked. The set is small and deliberately seeded; injected defects can be
easier to detect than real defects, so these recall figures are upper bounds for this exercise, not estimates
of real-world performance. Zero observed false positives also does not establish zero future false positives.
