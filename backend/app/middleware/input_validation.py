"""
Input validation middleware used by unit tests to block obvious SQLi/XSS vectors.
Lightweight, TESTING-safe, and no external deps.
"""

from __future__ import annotations

import re
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


_SQLI_PATTERNS = [
    re.compile(r";\s*drop\s+table", re.I),
    re.compile(r"\bunion\b\s+select", re.I),
    re.compile(r"\bor\b\s*'?1'?=\s*'?1'?", re.I),
]

_XSS_PATTERNS = [
    re.compile(r"<\s*script", re.I),
    re.compile(r"javascript:\s*", re.I),
    re.compile(r"onerror\s*=", re.I),
]


def _sanitize_str(value: str) -> str:
    # Remove common XSS vectors
    v = _XSS_PATTERNS[0].sub("", value)
    v = _XSS_PATTERNS[1].sub("", v)
    v = _XSS_PATTERNS[2].sub("", v)
    return v


class InputValidationMiddleware:
    """ASGI middleware variant to avoid BaseHTTPMiddleware body-consumption issues.
    Collects the request body, sanitizes, and re-injects a fresh receive channel.
    """
    def __init__(self, app: Callable):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http":
            await self.app(scope, receive, send)
            return

        # Build Request helper for convenience (safe for reading body once)
        request = Request(scope, receive=receive)

        # Basic SQLi check on query string; return 400 if blatant patterns
        for key, value in request.query_params.multi_items():
            if any(p.search(value or "") for p in _SQLI_PATTERNS):
                await send({
                    "type": "http.response.start",
                    "status": 400,
                    "headers": [(b"content-length", b"0")],
                })
                await send({"type": "http.response.body", "body": b""})
                return

        content_type = request.headers.get("content-type", "").lower()
        new_body_bytes: bytes | None = None
        if content_type.startswith("application/json"):
            try:
                import json as _jsonlib
                raw = await request.body()
                if raw:
                    body = _jsonlib.loads(raw.decode("utf-8"))
                    def scrub(obj):
                        if isinstance(obj, dict):
                            return {k: scrub(v) for k, v in obj.items()}
                        if isinstance(obj, list):
                            return [scrub(v) for v in obj]
                        if isinstance(obj, str):
                            return _sanitize_str(obj)
                        return obj
                    sanitized = scrub(body)
                    new_body_bytes = _jsonlib.dumps(sanitized).encode("utf-8")
            except Exception:
                # On malformed JSON, pass through and let downstream validation handle it
                new_body_bytes = None

        # Re-inject the (sanitized or original) body into a new receive() for downstream
        if new_body_bytes is None:
            # If we didn't build a new body, we still need to replay the original one
            # Fetch original bytes if not already loaded
            try:
                raw_fallback = await request.body()
            except Exception:
                raw_fallback = b""
            payload = raw_fallback
        else:
            payload = new_body_bytes

        done = {"sent": False}

        async def new_receive():
            if not done["sent"]:
                done["sent"] = True
                return {"type": "http.request", "body": payload, "more_body": False}
            return {"type": "http.request", "body": b"", "more_body": False}

        await self.app(scope, new_receive, send)


