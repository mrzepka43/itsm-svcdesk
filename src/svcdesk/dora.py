# ai-generated: 100% - implemented with an assistant from the Lab 2 metric specification
from __future__ import annotations

import re
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


def parse_instant(value: Any) -> datetime:
    if not isinstance(value, str) or RFC3339.fullmatch(value) is None:
        raise ValueError("timestamp must be an RFC 3339 instant with an offset")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00" if value.endswith("Z") else value)
    except ValueError as exc:
        raise ValueError("timestamp must be a valid RFC 3339 instant") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include an offset")
    return parsed.astimezone(timezone.utc)


def _require_string(value: Any, field: str, *, nullable: bool = False) -> None:
    if nullable and value is None:
        return
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")


def _round_decimal(value: Decimal, places: int) -> int | float:
    quantum = Decimal("1") if places == 0 else Decimal("1").scaleb(-places)
    rounded = value.quantize(quantum, rounding=ROUND_HALF_UP)
    return int(rounded) if places == 0 else float(rounded)


def _median_seconds(microseconds: list[int]) -> int | None:
    if not microseconds:
        return None
    ordered = sorted(microseconds)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        median_us = Decimal(ordered[middle])
    else:
        median_us = Decimal(ordered[middle - 1] + ordered[middle]) / 2
    return int(_round_decimal(median_us / Decimal(1_000_000), 0))


def _timedelta_us(delta: Any) -> int:
    return (delta.days * 86400 + delta.seconds) * 1_000_000 + delta.microseconds


def _duration_us(later: datetime, earlier: datetime) -> int:
    return max(0, _timedelta_us(later - earlier))


def _validate_events(raw_events: list[Any]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    seen_event_ids: set[str] = set()
    for raw in raw_events:
        if not isinstance(raw, dict):
            raise ValueError("each event must be an object")
        event_id = raw.get("event_id")
        if not isinstance(event_id, str) or not 1 <= len(event_id) <= 64:
            raise ValueError("event_id must contain 1..64 characters")
        if event_id in seen_event_ids:
            continue
        seen_event_ids.add(event_id)
        event = dict(raw)
        event["_at"] = parse_instant(raw.get("at"))
        event_type = raw.get("type")
        if event_type not in {"commit", "deployment", "incident"}:
            raise ValueError("event type must be commit, deployment, or incident")

        if event_type == "commit":
            _require_string(raw.get("sha"), "commit.sha")
            _require_string(raw.get("branch"), "commit.branch")
            _require_string(raw.get("reverts"), "commit.reverts", nullable=True)
            _require_string(raw.get("change_id"), "commit.change_id", nullable=True)
            if (raw.get("reverts") is None) == (raw.get("change_id") is None):
                raise ValueError("commit.change_id must be set exactly when reverts is null")
        elif event_type == "deployment":
            _require_string(raw.get("deployment_id"), "deployment.deployment_id")
            _require_string(raw.get("environment"), "deployment.environment")
            if raw.get("outcome") not in {"success", "failure"}:
                raise ValueError("deployment.outcome must be success or failure")
            commits = raw.get("commits")
            if not isinstance(commits, list) or any(not isinstance(sha, str) or not sha for sha in commits):
                raise ValueError("deployment.commits must be an array of non-empty strings")
            if not isinstance(raw.get("unplanned"), bool):
                raise ValueError("deployment.unplanned must be a boolean")
            _require_string(raw.get("caused_by"), "deployment.caused_by", nullable=True)
        else:
            _require_string(raw.get("incident_id"), "incident.incident_id")
            if raw.get("phase") not in {"opened", "resolved"}:
                raise ValueError("incident.phase must be opened or resolved")
            deployments = raw.get("deployments")
            if not isinstance(deployments, list) or any(not isinstance(item, str) or not item for item in deployments):
                raise ValueError("incident.deployments must be an array of non-empty strings")
        events.append(event)

    commits_by_sha: dict[str, dict[str, Any]] = {}
    deployments_by_id: dict[str, dict[str, Any]] = {}
    incidents_by_id: dict[str, dict[str, dict[str, Any]]] = {}
    for event in events:
        event_type = event["type"]
        if event_type == "commit":
            sha = event["sha"]
            if sha in commits_by_sha:
                raise ValueError("commit sha values must be unique")
            commits_by_sha[sha] = event
        elif event_type == "deployment":
            deployments_by_id.setdefault(event["deployment_id"], event)
        else:
            phases = incidents_by_id.setdefault(event["incident_id"], {})
            if event["phase"] in phases:
                raise ValueError("an incident may have at most one event per phase")
            phases[event["phase"]] = event

    for event in events:
        event_type = event["type"]
        if event_type == "commit" and event["reverts"] is not None and event["reverts"] not in commits_by_sha:
            raise ValueError("commit.reverts must name a sha in the log")
        if event_type == "deployment":
            if any(sha not in commits_by_sha for sha in event["commits"]):
                raise ValueError("deployment.commits must name shas in the log")
            if event["caused_by"] is not None and event["caused_by"] not in incidents_by_id:
                raise ValueError("deployment.caused_by must name an incident in the log")
        if event_type == "incident":
            if any(deployment_id not in deployments_by_id for deployment_id in event["deployments"]):
                raise ValueError("incident.deployments must name deployments in the log")

    if any("resolved" in phases and "opened" not in phases for phases in incidents_by_id.values()):
        raise ValueError("a resolved incident must also be opened")
    return events


def calculate_metrics(window: dict[str, Any], raw_events: list[Any]) -> dict[str, Any]:
    window_from = parse_instant(window.get("from"))
    window_to = parse_instant(window.get("to"))
    if window_to <= window_from:
        raise ValueError("window.to must be after window.from")
    events = _validate_events(raw_events)

    commits = {event["sha"]: event for event in events if event["type"] == "commit"}
    deployments = [
        event for event in events
        if event["type"] == "deployment"
        and event["environment"] == "production"
        and window_from <= event["_at"] < window_to
    ]
    deployments.sort(key=lambda event: (event["_at"], event["deployment_id"]))

    resolved_changes: dict[str, str] = {}

    def change_for(sha: str, active: set[str] | None = None) -> str:
        if sha in resolved_changes:
            return resolved_changes[sha]
        if active is None:
            active = set()
        if sha in active:
            raise ValueError("commit revert references must not form a cycle")
        active.add(sha)
        commit = commits[sha]
        change_id = commit["change_id"] if commit["reverts"] is None else change_for(commit["reverts"], active)
        active.remove(sha)
        resolved_changes[sha] = change_id
        return change_id

    all_changes: set[str] = set()
    first_commit_by_change: dict[str, datetime] = {}
    for sha, commit in commits.items():
        change_id = change_for(sha)
        all_changes.add(change_id)
        first_commit_by_change[change_id] = min(first_commit_by_change.get(change_id, commit["_at"]), commit["_at"])

    first_pair_shas: set[str] = set()
    lead_times_us: list[int] = []
    negative_lead_time_pairs = 0
    commits_never_on_main: set[str] = set()
    changes_delivered_at: dict[str, datetime] = {}
    for deployment in deployments:
        for sha in deployment["commits"]:
            commit = commits[sha]
            if commit["branch"] != "main":
                commits_never_on_main.add(sha)
            if deployment["outcome"] != "success":
                continue
            change_id = change_for(sha)
            changes_delivered_at[change_id] = min(
                changes_delivered_at.get(change_id, deployment["_at"]), deployment["_at"]
            )
            if sha not in first_pair_shas:
                first_pair_shas.add(sha)
                raw_delta = _timedelta_us(deployment["_at"] - commit["_at"])
                if raw_delta < 0:
                    negative_lead_time_pairs += 1
                lead_times_us.append(max(0, raw_delta))

    incidents: dict[str, dict[str, Any]] = {}
    for event in events:
        if event["type"] != "incident":
            continue
        incident = incidents.setdefault(event["incident_id"], {"deployments": set()})
        incident["deployments"].update(event["deployments"])
        incident[event["phase"]] = event["_at"]

    recovery_times_us: list[int] = []
    open_failures = 0
    failed_deployments = [event for event in deployments if event["outcome"] == "failure"]
    for deployment in failed_deployments:
        covering = [
            (incident["opened"], incident_id, incident)
            for incident_id, incident in incidents.items()
            if deployment["deployment_id"] in incident["deployments"] and "opened" in incident
        ]
        if not covering:
            open_failures += 1
            continue
        _, _, incident = min(covering, key=lambda item: (item[0], item[1].encode("utf-8")))
        if "resolved" not in incident:
            open_failures += 1
            continue
        recovery_times_us.append(_duration_us(incident["resolved"], deployment["_at"]))

    incident_intervals: list[tuple[datetime, datetime]] = []
    for incident in incidents.values():
        if "opened" not in incident:
            continue
        incident_intervals.append((incident["opened"], incident.get("resolved", window_to)))
    overlapping_incident_pairs = sum(
        1
        for index, (first_open, first_end) in enumerate(incident_intervals)
        for second_open, second_end in incident_intervals[index + 1:]
        if first_open < second_end and second_open < first_end
    )

    deployment_count = len(deployments)
    successful_count = sum(event["outcome"] == "success" for event in deployments)
    failed_count = len(failed_deployments)
    rework_count = sum(event["unplanned"] and event["caused_by"] is not None for event in deployments)
    empty_deployments = sum(not event["commits"] for event in deployments)
    window_seconds = Decimal(str((window_to - window_from).total_seconds()))
    window_days = window_seconds / Decimal(86400)
    changes_delivered = len(changes_delivered_at)
    true_lead_times_us = [
        _duration_us(delivered_at, first_commit_by_change[change_id])
        for change_id, delivered_at in changes_delivered_at.items()
    ]

    def rate(numerator: int) -> float | None:
        if deployment_count == 0:
            return None
        return float(_round_decimal(Decimal(numerator) / Decimal(deployment_count), 6))

    return {
        "spec_version": "1.0.0",
        "window": {"from": window["from"], "to": window["to"]},
        "deployment_frequency_per_day": float(_round_decimal(Decimal(deployment_count) / window_days, 6)),
        "change_lead_time_seconds_p50": _median_seconds(lead_times_us),
        "failed_deployment_recovery_time_seconds_p50": _median_seconds(recovery_times_us),
        "change_fail_rate": rate(failed_count),
        "deployment_rework_rate": rate(rework_count),
        "counts": {
            "deployments": deployment_count,
            "successful_deployments": successful_count,
            "failed_deployments": failed_count,
            "recovered_failures": len(recovery_times_us),
            "open_failures": open_failures,
            "rework_deployments": rework_count,
            "lead_time_pairs": len(lead_times_us),
            "changes": len(all_changes),
        },
        "anomalies": {
            "negative_lead_time_pairs": negative_lead_time_pairs,
            "deployments_without_commits": empty_deployments,
            "commits_never_on_main": len(commits_never_on_main),
            "revert_chains_collapsed": sum(commit["reverts"] is not None for commit in commits.values()),
            "overlapping_incident_pairs": overlapping_incident_pairs,
        },
        "ground_truth": {
            "changes_delivered": changes_delivered,
            "true_change_lead_time_seconds_p50": _median_seconds(true_lead_times_us),
        },
    }