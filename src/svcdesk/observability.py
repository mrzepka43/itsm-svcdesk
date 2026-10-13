# ai-generated: 85% - GitHub Copilot wrote the middleware and the /kb/search proxy, I specified the Lab 3 rules and reviewed it
from __future__ import annotations

import os
import time
from typing import Any

import httpx
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Histogram, generate_latest

KB_INDEX_URL = os.environ.get("KB_INDEX_URL", "http://kb-index:8080").rstrip("/")
UPSTREAM_TIMEOUT_SECONDS = 3.0
CATCH_ALL_ROUTE = "/{path:path}"

BUCKETS = (
    0.005, 0.01, 0.025, 0.05, 0.075, 0.09, 0.1, 0.11, 0.12, 0.13,
    0.14, 0.16, 0.2, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0,
)

registry = CollectorRegistry()
request_duration = Histogram(
    "http_server_request_duration_seconds",
    "Duration of HTTP server requests.",
    ["http_request_method", "http_route", "http_response_status_code"],
    buckets=BUCKETS,
    registry=registry,
)

router = APIRouter()
_client: httpx.AsyncClient | None = None


def get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=UPSTREAM_TIMEOUT_SECONDS,
            limits=httpx.Limits(max_connections=256, max_keepalive_connections=64),
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def route_template(scope: dict[str, Any]) -> str:
    route = scope.get("route")
    path = getattr(route, "path", None)
    if not path or path == CATCH_ALL_ROUTE:
        return "unmatched"
    return path


class MetricsMiddleware:
    """Pure ASGI middleware: observes every HTTP request exactly once, /metrics excepted."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] == "/metrics":
            await self.app(scope, receive, send)
            return

        start = time.perf_counter()
        status = {"code": 500}

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                status["code"] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            request_duration.labels(
                scope["method"], route_template(scope), str(status["code"])
            ).observe(time.perf_counter() - start)


def error(status: int, code: str, message: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message}})


@router.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)


@router.get("/kb/search")
async def kb_search(request: Request) -> JSONResponse:
    q = request.query_params.get("q")
    if q is None or not 1 <= len(q) <= 200:
        return error(400, "invalid_query", "q must be 1 to 200 characters")

    try:
        upstream = await get_client().get(f"{KB_INDEX_URL}/search", params={"q": q})
        if upstream.status_code != 200:
            raise httpx.HTTPError(f"upstream answered {upstream.status_code}")
        hits = upstream.json()["hits"]
    except (httpx.HTTPError, ValueError, KeyError):
        return error(502, "upstream_unavailable", "kb-index is unavailable")

    return JSONResponse(status_code=200, content={"query": q, "hits": hits})
