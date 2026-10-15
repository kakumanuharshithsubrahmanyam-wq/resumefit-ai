import time
from collections import defaultdict
from typing import DefaultDict, List

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.schemas.response import APIError, ErrorDetail


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory per-IP rate limiting ( suitable for single-instance deployments )."""

    def __init__(self, app, requests_per_minute: int) -> None:
        super().__init__(app)
        self.requests_per_minute = max(1, requests_per_minute)
        self._hits: DefaultDict[str, List[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.endswith("/health"):
            return await call_next(request)

        client_host = request.client.host if request.client else "unknown"
        now = time.time()
        window = [stamp for stamp in self._hits[client_host] if now - stamp < 60.0]
        if len(window) >= self.requests_per_minute:
            body = APIError(
                error=ErrorDetail(
                    code="rate_limit_exceeded",
                    message="Too many requests. Please retry in a moment.",
                ),
            )
            return JSONResponse(status_code=429, content=body.model_dump())

        window.append(now)
        self._hits[client_host] = window
        return await call_next(request)
