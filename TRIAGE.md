---
lab5_triage:
  image: ghcr.io/mrzepka43/itsm-svcdesk@sha256:8542f516492f471dc54d08e4a83101cd5b7992127d7f3e48f81fffcb232778d9
  sarif_receipt: 0
---
<!-- ai-generated: 100% - Copilot recorded the observed first-run findings and the corresponding changes -->
# Triage

The initial image scan on main reported the following fixable HIGH findings. The updated image passed the same
Trivy image gate locally and on the subsequent main run. The receipt, remaining scanner findings and bake-off
discussion will be added after the SARIF receipt and labels are available.

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

## Bake-off

Pending the canary run, SARIF receipt and revealed labels.
