# ai-generated: 100% -code wrote by AI.
import json
import os
import sys
import time
from urllib import error, request

BASE_URL = os.environ.get("SVCDESK_URL", "http://svcdesk:8080")


def read_json(url: str, method: str = "GET", body: dict | None = None, headers: dict | None = None):
    payload = None
    final_headers = {"Content-Type": "application/json"}
    if headers:
        final_headers.update(headers)
    if body is not None:
        payload = json.dumps(body).encode()
    req = request.Request(url, data=payload, headers=final_headers, method=method)
    try:
        with request.urlopen(req, timeout=10) as resp:
            data = resp.read().decode()
            return resp.status, json.loads(data) if data else {}
    except error.HTTPError as exc:
        try:
            body_text = exc.read().decode()
            payload = json.loads(body_text) if body_text else {}
        except Exception:
            payload = {}
        return exc.code, payload


def wait_for_service(timeout: float = 20.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            status, payload = read_json(f"{BASE_URL}/health")
            if status == 200 and payload.get("status") == "ok":
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def create_ticket(title: str, impact: int, urgency: int, vip: bool = False, clock: str = "2026-10-14T10:00:00Z"):
    payload = {
        "title": title,
        "description": f"test ticket {title}",
        "reporter": {"name": "Test Reporter", "email": "test@example.com", "vip": vip},
        "impact": impact,
        "urgency": urgency,
    }
    status, body = read_json(
        f"{BASE_URL}/tickets",
        method="POST",
        body=payload,
        headers={"X-Test-Clock": clock},
    )
    if status != 201:
        raise RuntimeError(f"create failed: {status} {body}")
    return body


def main():
    if not wait_for_service():
        print("ITSMLAB-TESTS: passed=0 failed=1")
        raise SystemExit(1)

    passed = 0
    failed = 0

    try:
        for idx in range(1, 11):
            ticket = create_ticket(f"Test ticket {idx}", 1 if idx % 2 else 2, 1 if idx % 3 else 2, vip=(idx % 2 == 0), clock=f"2026-10-14T10:{idx:02d}:00Z")
            if ticket.get("id") and ticket.get("priority"):
                passed += 1
            else:
                failed += 1
    except Exception as exc:  # pragma: no cover
        failed += 1
        print(f"ITSMLAB-TESTS: passed={passed} failed={failed}")
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    print(f"ITSMLAB-TESTS: passed={passed} failed={failed}")
    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
