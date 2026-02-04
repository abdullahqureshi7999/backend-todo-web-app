"""Centralized error handling middleware"""
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.exceptions.base import TodoAppException, TaskNotFoundError, UnauthorizedError


logger = logging.getLogger(__name__)


async def error_handler_middleware(request: Request, call_next):
    """Catch and handle exceptions globally"""
    try:
        return await call_next(request)
    except TaskNotFoundError as e:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": str(e), "code": "TASK_NOT_FOUND"}
        )
    except UnauthorizedError as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Unauthorized", "code": "UNAUTHORIZED"}
        )
    except TodoAppException as e:
        # Generic app exception
        logger.error(f"Application error: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(e), "code": "BAD_REQUEST"}
        )
    except Exception as e:
        # Unexpected error - log details, return generic message
        logger.error(f"Unhandled error: {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error", "code": "INTERNAL_ERROR"}
        )
