"""Health check endpoint"""
from fastapi import APIRouter
from pydantic import BaseModel


router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str
    service: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint to verify service is running"""
    return HealthResponse(
        status="ok",
        service="todo-backend"
    )
