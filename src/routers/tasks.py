"""Task API endpoints"""
from fastapi import APIRouter, Depends, status
from sqlmodel import Session, select, func
from typing import List
import logging

from src.db.database import get_session
from src.auth.dependencies import get_current_user
from src.schemas.task import TaskCreate, TaskUpdate, TaskRead, TaskListResponse
from src.crud import task as task_crud
from src.models.task import Task


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/todos", tags=["tasks"])


@router.post("/", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Create a new task"""
    task = task_crud.create_task(session, task_data, user_id)
    return task


@router.get("/", response_model=TaskListResponse)
async def list_tasks(
    search: str = None,
    status: str = "all",
    priority: str = "all",
    tags: list[str] = None,
    no_tags: bool = False,
    sort: str = "priority",
    order: str = None,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """List tasks for the authenticated user with filtering, searching, and sorting"""
    logger.info(f"Fetching tasks for user_id: {user_id}")

    # Count total tasks for the user (without filters for the total)
    total_statement = select(func.count(Task.id)).where(Task.user_id == user_id)
    total = session.exec(total_statement).one()
    logger.info(f"Total tasks for user {user_id}: {total}")

    # Get filtered tasks for the user (with filters applied)
    tasks = task_crud.list_tasks(
        session=session,
        user_id=user_id,
        search=search,
        status=status,
        priority=priority,
        tags=tags,
        no_tags=no_tags,
        sort_field=sort,
        sort_order=order or ("desc" if sort == "created_at" else "asc")
    )
    logger.info(f"Returning {len(tasks)} filtered tasks for user {user_id}")

    # For filtered count, we need to calculate the count based on the same filters
    # Build the same query but count instead of selecting
    query = select(func.count(Task.id)).where(Task.user_id == user_id)

    # Apply the same filters as in the main query
    if search:
        search_term = f"%{search}%"
        query = query.where(
            Task.title.ilike(search_term) |
            Task.description.ilike(search_term)
        )

    if status and status != "all":
        if status == "pending":
            query = query.where(Task.completed == False)
        elif status == "completed":
            query = query.where(Task.completed == True)

    if priority and priority != "all":
        query = query.where(Task.priority == priority)

    if tags:
        from src.models.tag import TaskTag, Tag
        query = query.join(TaskTag).join(Tag).where(
            Tag.name.in_(tags)
        )

    if no_tags:
        from src.models.tag import TaskTag
        query = query.outerjoin(TaskTag).where(TaskTag.task_id.is_(None))

    filtered = session.exec(query).one()

    return TaskListResponse(
        tasks=tasks,
        total=total,
        filtered=filtered
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: str,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Get a specific task by ID"""
    task = task_crud.get_task_with_tags(session, task_id, user_id)
    return task


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Update a task"""
    task = task_crud.update_task(session, task_id, task_data, user_id)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Delete a task"""
    task_crud.delete_task(session, task_id, user_id)


@router.post("/{task_id}/toggle", response_model=TaskRead)
async def toggle_task_completion(
    task_id: str,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """Toggle task completion status"""
    task = task_crud.toggle_task_completion(session, task_id, user_id)
    return task
