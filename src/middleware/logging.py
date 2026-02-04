"""Request/response logging middleware"""
import time
import logging
from fastapi import Request


logger = logging.getLogger(__name__)


async def logging_middleware(request: Request, call_next):
    """Log incoming requests and responses with timing"""
    start_time = time.time()

    # Log request
    logger.info(f"{request.method} {request.url.path}")

    # Process request
    response = await call_next(request)

    # Log response with timing
    duration = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} "
        f"status={response.status_code} duration={duration:.3f}s"
    )

    return response
