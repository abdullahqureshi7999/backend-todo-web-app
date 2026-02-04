"""User model - read-only reference to Better Auth user table

This model is NOT managed by this application.
Better Auth creates and manages the user table.
We reference it only for foreign key relationships.
"""
from sqlmodel import SQLModel, Field
from datetime import datetime, UTC


def utc_now() -> datetime:
    """Get current UTC time"""
    return datetime.now(UTC)


class User(SQLModel, table=True):
    """User model - managed by Better Auth"""

    id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    emailVerified: bool = Field(default=False)
    createdAt: datetime = Field(default_factory=utc_now)
    updatedAt: datetime = Field(default_factory=utc_now)

    class Config:
        """SQLModel configuration"""
        # This table is managed by Better Auth, not by us
        arbitrary_types_allowed = True
