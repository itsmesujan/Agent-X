"""Agent-X Structured Logging and Exception Handling Middleware."""

import logging
import time
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from agentx.kernel.state_machine import InvalidStateTransitionError

logger = logging.getLogger("agentx.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request-scoped correlation IDs and structured latency logging."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID", f"req_{uuid4().hex[:10]}")
        request.state.request_id = request_id

        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time-Ms"] = str(process_time_ms)

            logger.info(
                f"{request.method} {request.url.path} - status={response.status_code} "
                f"latency_ms={process_time_ms} req_id={request_id}"
            )
            return response
        except Exception as exc:
            process_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            logger.error(
                f"Unhandled Exception: {request.method} {request.url.path} - "
                f"error={str(exc)} latency_ms={process_time_ms} req_id={request_id}",
                exc_info=True,
            )
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected internal server error occurred.",
                        "request_id": request_id,
                    }
                },
                headers={"X-Request-ID": request_id},
            )


def register_exception_handlers(app: FastAPI) -> None:
    """Register uniform error response handlers across the FastAPI application."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        req_id = getattr(request.state, "request_id", f"req_{uuid4().hex[:10]}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": f"HTTP_{exc.status_code}",
                    "message": exc.detail,
                    "request_id": req_id,
                }
            },
            headers={"X-Request-ID": req_id},
        )

    @app.exception_handler(InvalidStateTransitionError)
    async def invalid_transition_handler(
        request: Request, exc: InvalidStateTransitionError
    ) -> JSONResponse:
        req_id = getattr(request.state, "request_id", f"req_{uuid4().hex[:10]}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_STATE_TRANSITION",
                    "message": str(exc),
                    "request_id": req_id,
                }
            },
            headers={"X-Request-ID": req_id},
        )
