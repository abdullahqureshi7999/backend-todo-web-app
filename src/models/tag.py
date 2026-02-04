"""Tag models for task categorization."""
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime, UTC
from typing import List, Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from src.models.task import Task


def utc_now() -> datetime:
    """Get current UTC time"""
    return datetime.now(UTC)


def generate_uuid() -> str:
    """Generate UUID string"""
    return str(uuid.uuid4())


class TaskTag(SQLModel, table=True):
    """
    Junction table for Task-Tag many-to-many relationship.

    Spec: 002-todo-organization-features
    Enables tasks to have multiple tags and tags to be on multiple tasks.

    NOTE: This must be defined BEFORE Tag and Task models to be used in link_model.
    """
    __tablename__ = "task_tag"

    # Composite primary key
    task_id: str = Field(foreign_key="task.id", primary_key=True)
    tag_id: str = Field(foreign_key="tag.id", primary_key=True)


class Tag(SQLModel, table=True):
    """
    Tag for categorizing tasks - unique per user, case-insensitive.

    Spec: 002-todo-organization-features
    Tags are stored lowercase and must be unique per user.
    """

    # Primary key
    id: str = Field(default_factory=generate_uuid, primary_key=True)

    # Foreign key - CRITICAL: All queries must filter by this
    user_id: str = Field(foreign_key="user.id", index=True)

    # Tag name (lowercase, no spaces, max 50 chars)
    name: str = Field(max_length=50, index=True)

    # Timestamp
    created_at: datetime = Field(default_factory=utc_now)

    # Relationship to tasks (via junction table)
    tasks: List["Task"] = Relationship(
        back_populates="tags",
        link_model=TaskTag
    )
