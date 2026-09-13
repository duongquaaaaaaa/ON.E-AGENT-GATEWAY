"""
Module 3 — Middleware
API key authentication, per-agent rate limiting, and audit logging.
"""

from __future__ import annotations
import json
import time
import uuid
import logging
from pathlib import Path
from collections import defaultdict
from datetime import datetime
from typing import Dict, Tuple, Optional

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# ── Logging ────────────────────────────────────────────────────────────
audit_logger = logging.getLogger("module3.audit")
audit_logger.setLevel(logging.INFO)

_log_file = LOGS_DIR / "audit.log"
_file_handler = logging.FileHandler(_log_file, encoding="utf-8")
_file_handler.setFormatter(logging.Formatter("%(message)s"))
audit_logger.addHandler(_file_handler)

# ── Load API Keys ──────────────────────────────────────────────────────
_keys_path = DATA_DIR / "api_keys.json"
_keys_data: dict = json.loads(_keys_path.read_text(encoding="utf-8"))

VALID_KEYS: Dict[str, dict] = {
    entry["key"]: entry for entry in _keys_data["keys"] if entry["active"]
}

# ── In-memory rate limit store: {agent_id: [(timestamp, count)]} ───────
_rate_buckets: Dict[str, list] = defaultdict(list)
WINDOW_SECONDS = 60


def _check_rate_limit(agent_id: str, limit: int) -> bool:
    """Sliding-window rate limit. Returns True if request is allowed."""
    now = time.time()
    bucket = _rate_buckets[agent_id]
    # Keep only timestamps within the last WINDOW_SECONDS
    bucket[:] = [t for t in bucket if now - t < WINDOW_SECONDS]
    if len(bucket) >= limit:
        return False
    bucket.append(now)
    return True


def log_audit(
    agent_id: str,
    endpoint: str,
    method: str,
    status_code: int,
    request_id: str,
    request_body: Optional[dict] = None,
    response_summary: Optional[str] = None,
):
    """Write a structured audit log entry."""
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "request_id": request_id,
        "agent_id": agent_id,
        "endpoint": endpoint,
        "method": method,
        "status_code": status_code,
        "response_summary": response_summary,
    }
    if request_body:
        entry["request_body"] = request_body
    audit_logger.info(json.dumps(entry))


class AgentAuthMiddleware(BaseHTTPMiddleware):
    """Validate X-Agent-Key header and enforce per-agent rate limiting."""

    # Paths that don't require auth
    EXEMPT_PATHS = {"/", "/health", "/docs", "/openapi.json", "/redoc"}

    async def dispatch(self, request: Request, call_next):
        # Skip auth for exempt paths
        if request.url.path in self.EXEMPT_PATHS:
            return await call_next(request)

        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # ── API Key Validation ─────────────────────────────────────────
        api_key = request.headers.get("X-Agent-Key")
        if not api_key or api_key not in VALID_KEYS:
            log_audit(
                agent_id="unknown",
                endpoint=request.url.path,
                method=request.method,
                status_code=401,
                request_id=request_id,
                response_summary="Unauthorized: invalid or missing X-Agent-Key",
            )
            return JSONResponse(
                status_code=401,
                content={"error": "Unauthorized", "detail": "Missing or invalid X-Agent-Key header"},
            )

        key_entry = VALID_KEYS[api_key]
        agent_id = key_entry["agent_id"]
        rate_limit = key_entry["rate_limit_per_minute"]

        request.state.agent_id = agent_id

        # ── Rate Limit Check ───────────────────────────────────────────
        if not _check_rate_limit(agent_id, rate_limit):
            log_audit(
                agent_id=agent_id,
                endpoint=request.url.path,
                method=request.method,
                status_code=429,
                request_id=request_id,
                response_summary=f"Rate limit exceeded ({rate_limit} req/min)",
            )
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Too Many Requests",
                    "detail": f"Rate limit of {rate_limit} requests/minute exceeded",
                },
                headers={"Retry-After": str(WINDOW_SECONDS)},
            )

        # ── Process Request ────────────────────────────────────────────
        response = await call_next(request)

        log_audit(
            agent_id=agent_id,
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            request_id=request_id,
            response_summary=f"HTTP {response.status_code}",
        )

        response.headers["X-Request-ID"] = request_id
        return response
