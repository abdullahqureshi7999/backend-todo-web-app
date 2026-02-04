"""
Tag API endpoints
Spec: 002-todo-organization-features
Task: T050
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session
from typing import List

from src.db.database import get_session
from src.auth.dependencies import get_current_user
from src.schemas.task import TagListResponse
from src.crud import tag as tag_crud

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.get("/", response_model=TagListResponse)
async def list_tags(
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List all tags for the authenticated user"""
    tag_stats = tag_crud.get_tag_stats(session, user_id)

    # Convert to the expected response format
    tags = [
        {"id": stat["id"], "name": stat["name"], "task_count": stat["task_count"]}
        for stat in tag_stats
    ]

    return {"tags": tags}
