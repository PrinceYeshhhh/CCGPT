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


class InputValidationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Response]) -> Response:
        # Validate query params
        for key, value in request.query_params.multi_items():
            if any(p.search(value or "") for p in _SQLI_PATTERNS):
                # Block blatant SQLi
                return Response(status_code=400)
        # Sanitize JSON body for XSS
        if request.headers.get("content-type", "").lower().startswith("application/json"):
            try:
                body = await request.json()
                def scrub(obj):
                    if isinstance(obj, dict):
                        return {k: scrub(v) for k, v in obj.items()}
                    if isinstance(obj, list):
                        return [scrub(v) for v in obj]
                    if isinstance(obj, str):
                        return _sanitize_str(obj)
                    return obj
                request._body = request._body if hasattr(request, "_body") else None  # keep attrs for safety
                request._json = scrub(body)
                async def _json_override():
                    return request._json
                request.json = _json_override  # type: ignore[assignment]
            except Exception:
                # Malformed JSON → allow downstream to handle 422
                pass
        return await call_next(request)


