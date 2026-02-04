"""Pydantic schemas for Task API requests/responses"""
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional
from enum import Enum

from src.models.priority import Priority


# Filter and Sort Enums
class StatusFilter(str, Enum):
    """Status filter options"""
    ALL = "all"
    PENDING = "pending"
    COMPLETED = "completed"


class PriorityFilter(str, Enum):
    """Priority filter options (includes 'all')"""
    ALL = "all"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"


class SortField(str, Enum):
    """Sort field options"""
    PRIORITY = "priority"
    TITLE = "title"
    CREATED_AT = "created_at"


class SortOrder(str, Enum):
    """Sort order options"""
    ASC = "asc"
    DESC = "desc"


class TaskCreate(BaseModel):
    """Schema for creating a new task"""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Priority = Field(default=Priority.NONE)
    tags: list[str] = Field(default_factory=list, max_length=20)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        """Validate tag format and convert to lowercase"""
        validated = []
        for tag in tags:
            tag = tag.strip()
            if not tag:
                continue
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds 50 characters")
            if ' ' in tag:
                raise ValueError(f"Tag '{tag}' contains spaces. Tags must be single words.")
            validated.append(tag.lower())
        # Remove duplicates while preserving order
        return list(dict.fromkeys(validated))


class TaskUpdate(BaseModel):
    """Schema for updating an existing task"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    completed: Optional[bool] = None
    priority: Optional[Priority] = None
    tags: Optional[list[str]] = Field(None, max_length=20)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, tags: Optional[list[str]]) -> Optional[list[str]]:
        """Validate tag format and convert to lowercase"""
        if tags is None:
            return None
        validated = []
        for tag in tags:
            tag = tag.strip()
            if not tag:
                continue
            if len(tag) > 50:
                raise ValueError(f"Tag '{tag}' exceeds 50 characters")
            if ' ' in tag:
                raise ValueError(f"Tag '{tag}' contains spaces. Tags must be single words.")
            validated.append(tag.lower())
        # Remove duplicates while preserving order
        return list(dict.fromkeys(validated))


class TaskRead(BaseModel):
    """Schema for task response"""
    id: str
    user_id: str
    title: str
    description: Optional[str]
    completed: bool
    priority: Priority
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime]

    @field_validator('tags', mode='before')
    @classmethod
    def serialize_tags(cls, tags):
        """Convert Tag objects to tag name strings"""
        if not tags:
            return []
        # If tags is already a list of strings, return it
        if isinstance(tags, list) and all(isinstance(t, str) for t in tags):
            return tags
        # If tags is a list of Tag objects, extract names
        if isinstance(tags, list):
            return [t.name if hasattr(t, 'name') else str(t) for t in tags]
        return []

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for list of tasks response"""
    tasks: list[TaskRead]
    total: int
    filtered: int


class TagRead(BaseModel):
    """Schema for tag response"""
    id: str
    name: str
    task_count: int


class TagListResponse(BaseModel):
    """Schema for list of tags response"""
    tags: list[TagRead]
