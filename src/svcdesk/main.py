# ai-generated: 85% - AI generated the service skeleton and I rewrote the logic to satisfy the Lab 1 contract, SLA rules, and state-machine checks
from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Optional
from zoneinfo import ZoneInfo

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

DB_PATH = os.environ.get("SVCDESK_DB", "/data/svcdesk.db")
WARSAW = ZoneInfo("Europe/Warsaw")
C1 = "wallclock"
C2 = "immutable"
C3 = "vip"

app = FastAPI(title="svcdesk")


def json_error(code: str, message: str, status: int = 400) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


def env_flag(value: Optional[str]) -> bool:
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def parse_rfc3339(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    dt = datetime.fromisoformat(value)
    if dt.tzinfo is None:
        raise ValueError("timestamp is missing timezone")
    return dt.astimezone(timezone.utc)


def iso_utc(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_request_clock(request: Request) -> datetime:
    enabled = env_flag(os.environ.get("SVCDESK_TEST_CLOCK"))
    if not enabled:
        return datetime.now(timezone.utc)

    header = request.headers.get("X-Test-Clock")
    if header is None:
        return datetime.now(timezone.utc)

    try:
        return parse_rfc3339(header)
    except Exception:
        raise ValueError("invalid X-Test-Clock header")


def ensure_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tickets (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            reporter_name TEXT NOT NULL,
            reporter_email TEXT,
            reporter_vip INTEGER NOT NULL DEFAULT 0,
            impact INTEGER NOT NULL,
            urgency INTEGER NOT NULL,
            priority TEXT NOT NULL,
            state TEXT NOT NULL,
            created_at TEXT NOT NULL,
            acknowledged_at TEXT,
            resolved_at TEXT,
            closed_at TEXT,
            related_to TEXT,
            ack_due_at TEXT NOT NULL,
            resolve_due_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def next_business_day(day: date) -> date:
    candidate = day
    for _ in range(7):
        candidate += timedelta(days=1)
        if candidate.weekday() < 5:
            return candidate
    return day


def next_business_start(current: datetime) -> datetime:
    local = current.astimezone(WARSAW)
    while True:
        if local.weekday() < 5:
            work_start = local.replace(hour=8, minute=0, second=0, microsecond=0)
            if local < work_start:
                return work_start
            if local.time() >= time(16, 0):
                candidate = (local.date() + timedelta(days=1))
                while candidate.weekday() >= 5:
                    candidate += timedelta(days=1)
                return datetime.combine(candidate, time(8, 0), tzinfo=WARSAW)
            return local
        candidate = (local.date() + timedelta(days=1))
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
        local = datetime.combine(candidate, time(8, 0), tzinfo=WARSAW)


def compute_business_due(created_at: datetime, target_minutes: int) -> datetime:
    remaining_seconds = target_minutes * 60
    current = created_at.astimezone(WARSAW)
    while True:
        current_date = current.date()
        if current_date.weekday() >= 5:
            next_day = current_date + timedelta(days=1)
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
            current = datetime.combine(next_day, time(8, 0), tzinfo=WARSAW)
            continue

        work_start = datetime.combine(current_date, time(8, 0), tzinfo=WARSAW)
        work_end = datetime.combine(current_date, time(16, 0), tzinfo=WARSAW)

        if current < work_start:
            current = work_start
        if current >= work_end:
            next_day = current_date + timedelta(days=1)
            while next_day.weekday() >= 5:
                next_day += timedelta(days=1)
            current = datetime.combine(next_day, time(8, 0), tzinfo=WARSAW)
            continue

        available_seconds = (work_end - current).total_seconds()
        if remaining_seconds <= available_seconds:
            return (current + timedelta(seconds=remaining_seconds)).astimezone(timezone.utc)

        remaining_seconds -= available_seconds
        next_day = current_date + timedelta(days=1)
        while next_day.weekday() >= 5:
            next_day += timedelta(days=1)
        current = datetime.combine(next_day, time(8, 0), tzinfo=WARSAW)


def compute_wallclock_due(created_at: datetime, target_minutes: int) -> datetime:
    return created_at + timedelta(minutes=target_minutes)


def priority_from_matrix(impact: int, urgency: int) -> str:
    matrix = {
        1: {1: "P1", 2: "P2", 3: "P3"},
        2: {1: "P2", 2: "P3", 3: "P4"},
        3: {1: "P3", 2: "P4", 3: "P4"},
    }
    return matrix[impact][urgency]


def compute_priority(impact: int, urgency: int, vip: bool) -> str:
    priority = priority_from_matrix(impact, urgency)
    if C3 == "vip" and vip and priority in {"P3", "P4"}:
        return "P2"
    return priority


def ticket_targets(created_at: datetime, priority: str) -> tuple[datetime, datetime]:
    ack_minutes = {"P1": 15, "P2": 60, "P3": 240, "P4": 480}
    resolve_minutes = {"P1": 240, "P2": 480, "P3": 1440, "P4": 4320}

    use_business_ack = (priority != "P1") or (C1 == "business")
    use_business_resolve = (priority != "P1") or (C1 == "business")

    ack_due = compute_business_due(created_at, ack_minutes[priority]) if use_business_ack else compute_wallclock_due(created_at, ack_minutes[priority])
    resolve_due = compute_business_due(created_at, resolve_minutes[priority]) if use_business_resolve else compute_wallclock_due(created_at, resolve_minutes[priority])
    return ack_due, resolve_due


def row_to_ticket(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "reporter": {
            "name": row["reporter_name"],
            "email": row["reporter_email"],
            "vip": bool(row["reporter_vip"]),
        },
        "impact": row["impact"],
        "urgency": row["urgency"],
        "priority": row["priority"],
        "state": row["state"],
        "created_at": row["created_at"],
        "acknowledged_at": row["acknowledged_at"],
        "resolved_at": row["resolved_at"],
        "closed_at": row["closed_at"],
        "related_to": row["related_to"],
        "sla": {
            "ack_due_at": row["ack_due_at"],
            "resolve_due_at": row["resolve_due_at"],
        },
    }


def state_transition_error(message: str = "invalid transition") -> JSONResponse:
    return json_error("invalid_transition", message, status=409)


def get_ticket_or_404(ticket_id: str) -> sqlite3.Row:
    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    if row is None:
        raise KeyError(ticket_id)
    return row


def is_business_window(now: datetime) -> bool:
    local = now.astimezone(WARSAW)
    if local.weekday() >= 5:
        return False
    return time(8, 0) <= local.time() < time(16, 0)


def resolution_uses_business(priority: str) -> bool:
    if C1 == "business":
        return True
    return priority != "P1"


@app.on_event("startup")
async def startup_event() -> None:
    ensure_db()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "svcdesk"}


@app.post("/tickets")
async def create_ticket(request: Request) -> JSONResponse:
    try:
        body = await request.body()
        if not body:
            return json_error("validation", "request body is required", status=422)
        payload = json.loads(body)
    except Exception:
        return json_error("validation", "request body must be valid JSON", status=422)

    if not isinstance(payload, dict):
        return json_error("validation", "request body must be an object", status=422)

    title = payload.get("title")
    if not isinstance(title, str) or len(title.strip()) == 0 or len(title) > 200:
        return json_error("validation", "title is required", status=422)

    description = payload.get("description", "")
    if description is None:
        description = ""
    if not isinstance(description, str) or len(description) > 4000:
        return json_error("validation", "description is too long", status=422)

    reporter = payload.get("reporter")
    if not isinstance(reporter, dict):
        return json_error("validation", "reporter is required", status=422)

    reporter_name = reporter.get("name")
    if not isinstance(reporter_name, str) or len(reporter_name.strip()) == 0 or len(reporter_name) > 100:
        return json_error("validation", "reporter.name is required", status=422)

    reporter_email = reporter.get("email")
    if reporter_email is not None and not isinstance(reporter_email, str):
        return json_error("validation", "reporter.email must be a string or null", status=422)

    reporter_vip = reporter.get("vip", False)
    if not isinstance(reporter_vip, bool):
        return json_error("validation", "reporter.vip must be a boolean", status=422)

    impact = payload.get("impact")
    if not isinstance(impact, int) or impact not in {1, 2, 3}:
        return json_error("validation", "impact must be an integer in 1..3", status=422)

    urgency = payload.get("urgency")
    if not isinstance(urgency, int) or urgency not in {1, 2, 3}:
        return json_error("validation", "urgency must be an integer in 1..3", status=422)

    try:
        now = get_request_clock(request)
    except ValueError:
        return json_error("validation", "X-Test-Clock is invalid", status=422)

    ticket_id = str(uuid.uuid4())
    priority = compute_priority(impact, urgency, bool(reporter_vip))
    ack_due, resolve_due = ticket_targets(now, priority)

    conn = get_conn()
    conn.execute(
        """
        INSERT INTO tickets (
            id, title, description, reporter_name, reporter_email, reporter_vip,
            impact, urgency, priority, state, created_at, acknowledged_at, resolved_at,
            closed_at, related_to, ack_due_at, resolve_due_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticket_id,
            title,
            description,
            reporter_name,
            reporter_email,
            int(reporter_vip),
            impact,
            urgency,
            priority,
            "new",
            iso_utc(now),
            None,
            None,
            None,
            payload.get("related_to"),
            iso_utc(ack_due),
            iso_utc(resolve_due),
        ),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return JSONResponse(status_code=201, content=row_to_ticket(row))


@app.get("/tickets")
async def list_tickets(request: Request) -> list[dict[str, Any]]:
    state = request.query_params.get("state")
    priority = request.query_params.get("priority")

    query = "SELECT * FROM tickets"
    params: list[Any] = []
    clauses: list[str] = []
    if state:
        clauses.append("state = ?")
        params.append(state)
    if priority:
        clauses.append("priority = ?")
        params.append(priority)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY created_at"

    conn = get_conn()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [row_to_ticket(r) for r in rows]


@app.get("/tickets/{ticket_id}")
async def get_ticket(ticket_id: str) -> JSONResponse:
    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    if row is None:
        return json_error("not_found", "ticket not found", status=404)
    return JSONResponse(content=row_to_ticket(row))


@app.post("/tickets/{ticket_id}/ack")
async def ack_ticket(ticket_id: str, request: Request) -> JSONResponse:
    try:
        now = get_request_clock(request)
    except ValueError:
        return json_error("validation", "X-Test-Clock is invalid", status=422)

    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        conn.close()
        return json_error("not_found", "ticket not found", status=404)
    if row["state"] != "new":
        conn.close()
        return state_transition_error("acknowledgement requires a new ticket")

    conn.execute(
        "UPDATE tickets SET state = ?, acknowledged_at = ? WHERE id = ?",
        ("acknowledged", iso_utc(now), ticket_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return JSONResponse(content=row_to_ticket(updated))


@app.post("/tickets/{ticket_id}/start")
async def start_ticket(ticket_id: str, request: Request) -> JSONResponse:
    try:
        now = get_request_clock(request)
    except ValueError:
        return json_error("validation", "X-Test-Clock is invalid", status=422)

    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        conn.close()
        return json_error("not_found", "ticket not found", status=404)
    if row["state"] != "acknowledged":
        conn.close()
        return state_transition_error("start requires an acknowledged ticket")

    conn.execute("UPDATE tickets SET state = ? WHERE id = ?", ("in_progress", ticket_id))
    conn.commit()
    updated = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return JSONResponse(content=row_to_ticket(updated))


@app.post("/tickets/{ticket_id}/resolve")
async def resolve_ticket(ticket_id: str, request: Request) -> JSONResponse:
    try:
        now = get_request_clock(request)
    except ValueError:
        return json_error("validation", "X-Test-Clock is invalid", status=422)

    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        conn.close()
        return json_error("not_found", "ticket not found", status=404)
    if row["state"] != "in_progress":
        conn.close()
        return state_transition_error("resolution requires an in_progress ticket")

    conn.execute(
        "UPDATE tickets SET state = ?, resolved_at = ? WHERE id = ?",
        ("resolved", iso_utc(now), ticket_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return JSONResponse(content=row_to_ticket(updated))


@app.post("/tickets/{ticket_id}/close")
async def close_ticket(ticket_id: str, request: Request) -> JSONResponse:
    try:
        now = get_request_clock(request)
    except ValueError:
        return json_error("validation", "X-Test-Clock is invalid", status=422)

    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        conn.close()
        return json_error("not_found", "ticket not found", status=404)
    if row["state"] != "resolved":
        conn.close()
        return state_transition_error("close requires a resolved ticket")

    conn.execute(
        "UPDATE tickets SET state = ?, closed_at = ? WHERE id = ?",
        ("closed", iso_utc(now), ticket_id),
    )
    conn.commit()
    updated = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return JSONResponse(content=row_to_ticket(updated))


@app.post("/tickets/{ticket_id}/reopen")
async def reopen_ticket(ticket_id: str, request: Request) -> JSONResponse:
    try:
        now = get_request_clock(request)
    except ValueError:
        return json_error("validation", "X-Test-Clock is invalid", status=422)

    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        conn.close()
        return json_error("not_found", "ticket not found", status=404)

    state = row["state"]
    if state == "resolved":
        resolved_at = parse_rfc3339(row["resolved_at"]) if row["resolved_at"] else now
        if now > resolved_at + timedelta(days=7):
            conn.close()
            return state_transition_error("reopen_window_expired")
        conn.execute(
            "UPDATE tickets SET state = ?, resolved_at = NULL WHERE id = ?",
            ("in_progress", ticket_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        conn.close()
        return JSONResponse(content=row_to_ticket(updated))

    if state == "closed":
        if C2 != "reopen":
            conn.close()
            return state_transition_error("ticket is immutable")
        closed_at = parse_rfc3339(row["closed_at"]) if row["closed_at"] else now
        if now > closed_at + timedelta(days=7):
            conn.close()
            return state_transition_error("reopen_window_expired")
        conn.execute(
            "UPDATE tickets SET state = ?, closed_at = NULL WHERE id = ?",
            ("in_progress", ticket_id),
        )
        conn.commit()
        updated = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
        conn.close()
        return JSONResponse(content=row_to_ticket(updated))

    conn.close()
    return state_transition_error("reopen requires a resolved or closed ticket")


@app.get("/tickets/{ticket_id}/sla")
async def get_ticket_sla(ticket_id: str, request: Request) -> JSONResponse:
    try:
        now = get_request_clock(request)
    except ValueError:
        return json_error("validation", "X-Test-Clock is invalid", status=422)

    conn = get_conn()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    if row is None:
        return json_error("not_found", "ticket not found", status=404)

    ack_due = parse_rfc3339(row["ack_due_at"])
    resolve_due = parse_rfc3339(row["resolve_due_at"])
    acked_at = parse_rfc3339(row["acknowledged_at"]) if row["acknowledged_at"] else None
    resolved_at = parse_rfc3339(row["resolved_at"]) if row["resolved_at"] else None

    ack_breached = False
    if acked_at is None:
        ack_breached = now > ack_due
    else:
        ack_breached = acked_at > ack_due

    resolve_breached = False
    if resolved_at is None:
        if row["state"] == "resolved":
            resolve_breached = now > resolve_due
        else:
            resolve_breached = now > resolve_due
    else:
        resolve_breached = resolved_at > resolve_due

    paused = False
    if row["state"] not in {"resolved", "closed"} and resolution_uses_business(row["priority"]) and not is_business_window(now):
        paused = True

    return JSONResponse(
        content={
            "priority": row["priority"],
            "ack_due_at": row["ack_due_at"],
            "resolve_due_at": row["resolve_due_at"],
            "ack_breached": ack_breached,
            "resolve_breached": resolve_breached,
            "paused": paused,
        }
    )


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"])
async def catch_all(path: str, request: Request) -> JSONResponse:
    return json_error("not_found", f"route not found: {request.url.path}", status=404)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("svcdesk.main:app", host="0.0.0.0", port=8080, reload=False)
