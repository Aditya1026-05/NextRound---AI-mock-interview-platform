import time
import uuid

import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.observability import bind_context, clear_context

logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """FastAPI Middleware to intercept all incoming requests,
    generate unique Request IDs, track request duration,
    and propagate correlation headers.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())
        client_ip = request.client.host if request.client else "unknown"

        # Initialize thread-local logger contexts
        clear_context()
        bind_context(request_id=request_id)
        structlog.contextvars.bind_contextvars(client_ip=client_ip)

        method = request.method
        path = request.url.path

        logger.info(
            f"REQUEST START - {method} {path} - IP: {client_ip}",
            category="API",
            method=method,
            path=path,
            client_ip=client_ip,
            status="started",
        )

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            status_code = response.status_code

            logger.info(
                f"REQUEST END - {method} {path} - Status: {status_code} - Latency: {duration:.3f}s",
                category="API",
                status_code=status_code,
                duration_seconds=duration,
                status="completed",
            )

            response.headers["Request-ID"] = request_id
            return response

        except Exception as e:
            duration = time.perf_counter() - start_time
            logger.error(
                f"REQUEST END FAILED - {method} {path} - Latency: {duration:.3f}s",
                category="API",
                duration_seconds=duration,
                status="failed",
                error=str(e),
            )
            raise e
