"""Middleware adding CORS headers based on the dynamic origin registry.

Unlike Starlette's ``CORSMiddleware`` (fixed origin list at startup), this
reads the allowlist from ``app.origins`` on every request, so origins added
through the admin panel take effect immediately without a restart.
"""

import logging

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.origins import is_allowed

logger = logging.getLogger(__name__)


class DynamicCorsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        try:
            if request.method == "OPTIONS":
                response = Response(status_code=204)
            else:
                response = await call_next(request)
        except Exception:
            # Unhandled errors must still produce a CORS-eligible response,
            # otherwise the browser reports them as opaque CORS failures
            # instead of the real 500.
            logger.exception(
                "Unhandled error while serving %s %s",
                request.method,
                request.url.path,
            )
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"},
            )
        if origin and is_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "*"
            response.headers["Access-Control-Max-Age"] = "600"
            response.headers["Vary"] = "Origin"
        return response
