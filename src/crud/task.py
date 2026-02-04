"""CRUD operations for Task model"""
from sqlmodel import Session, select, case
from sqlalchemy.orm import selectinload
from src.models.task import Task
from src.models.tag import Tag, TaskTag
from src.models.priority import Priority, PRIORITY_SORT_ORDER
from src.schemas.task import TaskCreate, TaskUpdate
from src.exceptions.base import TaskNotFoundError, UnauthorizedError
from datetime import datetime, UTC
from typing import List, Optional


def _get_or_create_tag(session: Session, tag_name: str, user_id: str) -> Tag:
    """
    Get an existing tag or create a new one (case-insensitive)

    Args:
        session: Database session
        tag_name: Tag name (will be converted to lowercase)
        user_id: ID of the user

    Returns:
        Tag instance
    """
    tag_name = tag_name.lower().strip()

    # Try to find existing tag
    statement = select(Tag).where(
        Tag.user_id == user_id,
        Tag.name == tag_name
    )
    tag = session.exec(statement).first()

    if not tag:
        # Create new tag
        tag = Tag(user_id=user_id, name=tag_name)
        session.add(tag)
        session.flush()  # Flush to get the ID

    return tag


def create_task(session: Session, task_data: TaskCreate, user_id: str) -> Task:
    """
    Create a new task for a user

    Args:
        session: Database session
        task_data: Task creation data
        user_id: ID of the user creating the task

    Returns:
        Created task with tags
    """
    task = Task(
        user_id=user_id,
        title=task_data.title,
        description=task_data.description,
        priority=task_data.priority,
    )
    session.add(task)
    session.flush()  # Flush to get task ID

    # Handle tags if provided
    if task_data.tags:
        for tag_name in task_data.tags:
            tag = _get_or_create_tag(session, tag_name, user_id)
            # Create TaskTag relationship
            task_tag = TaskTag(task_id=task.id, tag_id=tag.id)
            session.add(task_tag)

    session.commit()
    session.refresh(task)
    return task


def _load_task_tags(session: Session, task: Task) -> List[str]:
    """
    Load tag names for a task

    Args:
        session: Database session
        task: Task instance

    Returns:
        List of tag names
    """
    statement = (
        select(Tag.name)
        .join(TaskTag, TaskTag.tag_id == Tag.id)
        .where(TaskTag.task_id == task.id)
    )
    tag_names = session.exec(statement).all()
    return list(tag_names)


def get_task(session: Session, task_id: str, user_id: str) -> Task:
    """
    Get a task by ID, ensuring it belongs to the user

    Args:
        session: Database session
        task_id: ID of the task
        user_id: ID of the user

    Returns:
        Task if found and belongs to user

    Raises:
        TaskNotFoundError: If task doesn't exist or doesn't belong to user
    """
    statement = select(Task).where(
        Task.id == task_id,
        Task.user_id == user_id
    )
    task = session.exec(statement).first()

    if not task:
        raise TaskNotFoundError(task_id)

    return task


def get_task_with_tags(session: Session, task_id: str, user_id: str) -> Task:
    """
    Get a task by ID with its tags, ensuring it belongs to the user

    Args:
        session: Database session
        task_id: ID of the task
        user_id: ID of the user

    Returns:
        Task with tags if found and belongs to user

    Raises:
        TaskNotFoundError: If task doesn't exist or doesn't belong to user
    """
    statement = select(Task).where(
        Task.id == task_id,
        Task.user_id == user_id
    ).options(
        selectinload(Task.tags)
    )
    task = session.exec(statement).first()

    if not task:
        raise TaskNotFoundError(task_id)

    # Tags will be loaded through the SQLAlchemy relationship
    return task


def list_tasks(
    session: Session,
    user_id: str,
    search: str = None,
    status: str = None,
    priority: str = None,
    tags: list = None,
    no_tags: bool = False,
    sort_field: str = "priority",
    sort_order: str = "asc"
) -> List[Task]:
    """
    List tasks for a user with filtering, searching, and sorting options

    Args:
        session: Database session
        user_id: ID of the user
        search: Search term to match in title or description
        status: Filter by status ("all", "pending", "completed")
        priority: Filter by priority ("all", "high", "medium", "low", "none")
        tags: Filter by tags (OR logic)
        no_tags: Filter for tasks without tags
        sort_field: Field to sort by ("priority", "title", "created_at")
        sort_order: Sort order ("asc", "desc")

    Returns:
        List of tasks with applied filters and sorting
    """
    # Build query with eager loading of tags
    statement = select(Task).where(Task.user_id == user_id).options(
        selectinload(Task.tags)
    )

    # Apply search filter
    if search:
        search_term = f"%{search}%"
        statement = statement.where(
            Task.title.ilike(search_term) |
            Task.description.ilike(search_term)
        )

    # Apply status filter
    if status and status != "all":
        if status == "pending":
            statement = statement.where(Task.completed == False)
        elif status == "completed":
            statement = statement.where(Task.completed == True)

    # Apply priority filter
    if priority and priority != "all":
        statement = statement.where(Task.priority == priority)

    # Apply tags filter
    if tags:
        from src.models.tag import TaskTag
        # Find tasks that have any of the specified tags
        statement = statement.join(TaskTag).join(Tag).where(
            Tag.name.in_(tags)
        )

    # Apply no_tags filter
    if no_tags:
        from src.models.tag import TaskTag
        # Find tasks that have no tags
        statement = statement.outerjoin(TaskTag).where(TaskTag.task_id.is_(None))

    # Apply sorting
    if sort_field == "priority":
        # Priority sort order: HIGH -> MEDIUM -> LOW -> NONE
        priority_order = case(
            (Task.priority == Priority.HIGH, 0),
            (Task.priority == Priority.MEDIUM, 1),
            (Task.priority == Priority.LOW, 2),
            (Task.priority == Priority.NONE, 3),
            else_=4
        )
        if sort_order == "desc":
            statement = statement.order_by(priority_order.desc(), Task.created_at.desc())
        else:
            statement = statement.order_by(priority_order, Task.created_at.desc())
    elif sort_field == "title":
        if sort_order == "desc":
            statement = statement.order_by(Task.title.desc())
        else:
            statement = statement.order_by(Task.title.asc())
    elif sort_field == "created_at":
        if sort_order == "desc":
            statement = statement.order_by(Task.created_at.desc())
        else:
            statement = statement.order_by(Task.created_at.asc())

    tasks = session.exec(statement).all()
    task_list = list(tasks)

    # Tags will be loaded through the SQLAlchemy relationship
    # and serialized by the TaskRead schema
    return task_list


def update_task(session: Session, task_id: str, task_data: TaskUpdate, user_id: str) -> Task:
    """
    Update a task

    Args:
        session: Database session
        task_id: ID of the task
        task_data: Updated task data
        user_id: ID of the user

    Returns:
        Updated task

    Raises:
        TaskNotFoundError: If task doesn't exist or doesn't belong to user
    """
    task = get_task(session, task_id, user_id)

    # Update only provided fields
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.completed is not None:
        task.completed = task_data.completed
    if task_data.priority is not None:
        task.priority = task_data.priority

    # Update tags if provided
    if task_data.tags is not None:
        # Remove existing tag relationships
        statement = select(TaskTag).where(TaskTag.task_id == task_id)
        existing_task_tags = session.exec(statement).all()
        for task_tag in existing_task_tags:
            session.delete(task_tag)

        # Add new tag relationships
        for tag_name in task_data.tags:
            tag = _get_or_create_tag(session, tag_name, user_id)
            task_tag = TaskTag(task_id=task.id, tag_id=tag.id)
            session.add(task_tag)

    task.updated_at = datetime.now(UTC)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task_id: str, user_id: str) -> None:
    """
    Delete a task

    Args:
        session: Database session
        task_id: ID of the task
        user_id: ID of the user

    Raises:
        TaskNotFoundError: If task doesn't exist or doesn't belong to user
    """
    task = get_task(session, task_id, user_id)
    session.delete(task)
    session.commit()


def toggle_task_completion(session: Session, task_id: str, user_id: str) -> Task:
    """
    Toggle task completion status

    Args:
        session: Database session
        task_id: ID of the task
        user_id: ID of the user

    Returns:
        Updated task

    Raises:
        TaskNotFoundError: If task doesn't exist or doesn't belong to user
    """
    task = get_task(session, task_id, user_id)
    task.completed = not task.completed
    task.updated_at = datetime.now(UTC)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task
