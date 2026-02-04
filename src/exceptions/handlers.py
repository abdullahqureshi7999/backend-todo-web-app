"""Exception handlers for FastAPI"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from src.exceptions.base import TaskNotFoundError, UnauthorizedError, ValidationError
import logging


logger = logging.getLogger(__name__)


async def task_not_found_handler(request: Request, exc: TaskNotFoundError) -> JSONResponse:
    """Handle TaskNotFoundError"""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "code": "TASK_NOT_FOUND"}
    )


async def unauthorized_handler(request: Request, exc: UnauthorizedError) -> JSONResponse:
    """Handle UnauthorizedError"""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={"detail": str(exc), "code": "UNAUTHORIZED"}
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle ValidationError"""
    content = {"detail": str(exc), "code": "VALIDATION_ERROR"}
    if exc.field:
        content["field"] = exc.field
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content
    )
