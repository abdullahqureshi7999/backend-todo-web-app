"""Task model for todo items"""
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, Enum as SQLEnum
from datetime import datetime, UTC
from typing import Optional, List, TYPE_CHECKING
import uuid

from src.models.priority import Priority
# Import TaskTag before Task to use it in link_model
from src.models.tag import TaskTag

if TYPE_CHECKING:
    from src.models.tag import Tag


def utc_now() -> datetime:
    """Get current UTC time"""
    return datetime.now(UTC)


def generate_uuid() -> str:
    """Generate UUID string"""
    return str(uuid.uuid4())


class Task(SQLModel, table=True):
    """
    Task model for user todo items.

    Spec: 002-todo-organization-features
    Extended from 001-todo-web-crud with:
    - priority field (enum)
    - tags relationship (many-to-many)
    """

    # Primary key
    id: str = Field(default_factory=generate_uuid, primary_key=True)

    # Foreign key - CRITICAL: All queries must filter by this
    user_id: str = Field(foreign_key="user.id", index=True)

    # Task content
    title: str = Field(max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)

    # Status
    completed: bool = Field(default=False)

    # Priority level (NEW)
    # Using sa_column to ensure SQLAlchemy uses the string values ("none", "low", etc)
    # not the enum names (NONE, LOW, etc)
    priority: Priority = Field(
        default=Priority.NONE,
        sa_column=Column(
            SQLEnum(Priority, native_enum=False, values_callable=lambda x: [e.value for e in x]),
            index=True
        )
    )

    # Timestamps
    created_at: datetime = Field(default_factory=utc_now, index=True)
    updated_at: Optional[datetime] = Field(default=None)

    # Relationship to tags (via junction table)
    tags: List["Tag"] = Relationship(
        back_populates="tasks",
        link_model=TaskTag
    )
