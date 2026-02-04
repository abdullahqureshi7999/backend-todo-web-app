"""FastAPI application entry point"""
from fastapi import FastAPI
from src.config import settings
from src.db.database import create_db_and_tables
from src.middleware.cors import configure_cors
from src.middleware.logging import logging_middleware
from src.middleware.error_handler import error_handler_middleware
from src.routers import health, tasks, tags
from src.exceptions.base import TaskNotFoundError, UnauthorizedError, ValidationError
from src.exceptions.handlers import (
    task_not_found_handler,
    unauthorized_handler,
    validation_error_handler,
)
import logging


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
)


# Configure middleware (order matters: first added = outermost layer)
app.middleware("http")(logging_middleware)  # 1. Log first
app.middleware("http")(error_handler_middleware)  # 2. Handle errors
configure_cors(app)  # 3. CORS last


# Register exception handlers
app.add_exception_handler(TaskNotFoundError, task_not_found_handler)
app.add_exception_handler(UnauthorizedError, unauthorized_handler)
app.add_exception_handler(ValidationError, validation_error_handler)


# Register routers
app.include_router(health.router)
app.include_router(tasks.router)
app.include_router(tags.router)


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Starting up Todo Backend API...")
    # Create database tables
    create_db_and_tables()
    logger.info("Database tables created/verified")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down Todo Backend API...")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Todo Backend API",
        "docs": "/docs",
        "health": "/health"
    }
