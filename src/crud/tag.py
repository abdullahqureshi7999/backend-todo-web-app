"""
CRUD operations for Tag model
Spec: 002-todo-organization-features
Task: T045
"""
from sqlmodel import Session, select
from src.models.tag import Tag
from src.schemas.task import TagRead
from src.exceptions.base import TagNotFoundError
from datetime import datetime, UTC
from typing import List


def get_or_create_tag(session: Session, tag_name: str, user_id: str) -> Tag:
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


def get_tag_by_id(session: Session, tag_id: str, user_id: str) -> Tag:
    """
    Get a tag by ID, ensuring it belongs to the user

    Args:
        session: Database session
        tag_id: ID of the tag
        user_id: ID of the user

    Returns:
        Tag if found and belongs to user

    Raises:
        TagNotFoundError: If tag doesn't exist or doesn't belong to user
    """
    statement = select(Tag).where(
        Tag.id == tag_id,
        Tag.user_id == user_id
    )
    tag = session.exec(statement).first()

    if not tag:
        raise TagNotFoundError(tag_id)

    return tag


def list_tags(session: Session, user_id: str) -> List[Tag]:
    """
    List all tags for a user

    Args:
        session: Database session
        user_id: ID of the user

    Returns:
        List of tags ordered by name (alphabetically)
    """
    statement = select(Tag).where(
        Tag.user_id == user_id
    ).order_by(Tag.name.asc())

    tags = session.exec(statement).all()
    return list(tags)


def get_tags_for_task(session: Session, task_id: str, user_id: str) -> List[Tag]:
    """
    Get all tags associated with a task

    Args:
        session: Database session
        task_id: ID of the task
        user_id: ID of the user

    Returns:
        List of tags associated with the task
    """
    from src.models.task import Task, TaskTag

    # First verify the task belongs to the user
    statement = select(Task).where(
        Task.id == task_id,
        Task.user_id == user_id
    )
    task = session.exec(statement).first()

    if not task:
        raise TagNotFoundError(f"Task {task_id} not found for user {user_id}")

    # Get tags for the task
    statement = select(Tag).join(
        TaskTag, TaskTag.tag_id == Tag.id
    ).where(
        TaskTag.task_id == task_id
    ).order_by(Tag.name.asc())

    tags = session.exec(statement).all()
    return list(tags)


def get_tag_stats(session: Session, user_id: str) -> List[dict]:
    """
    Get tag statistics (including task count)

    Args:
        session: Database session
        user_id: ID of the user

    Returns:
        List of dictionaries with tag info and task count
    """
    from sqlalchemy import func
    from src.models.task import TaskTag

    statement = select(
        Tag.id,
        Tag.name,
        func.count(TaskTag.task_id).label('task_count')
    ).outerjoin(
        TaskTag, TaskTag.tag_id == Tag.id
    ).where(
        Tag.user_id == user_id
    ).group_by(
        Tag.id, Tag.name
    ).order_by(Tag.name.asc())

    results = session.exec(statement).all()
    return [
        {"id": r.id, "name": r.name, "task_count": r.task_count}
        for r in results
    ]


def cleanup_orphan_tags(session: Session, user_id: str) -> int:
    """
    Clean up orphan tags (tags with no associated tasks)

    Args:
        session: Database session
        user_id: ID of the user

    Returns:
        Number of tags deleted
    """
    from src.models.task import TaskTag
    from sqlalchemy import exists

    # Find tags that have no associated tasks
    statement = select(Tag).where(
        Tag.user_id == user_id
    ).where(
        ~exists().where(TaskTag.tag_id == Tag.id)
    )

    orphan_tags = session.exec(statement).all()
    count = 0

    for tag in orphan_tags:
        session.delete(tag)
        count += 1

    if count > 0:
        session.commit()

    return count
