# Backend Development Guide

This guide defines development standards for the FastAPI backend application.

## API Standards

### Response Format
- **Always JSON**: All endpoints return JSON responses
- **Consistent Structure**: Use Pydantic models for request/response schemas
- **Error Format**: `{"detail": "Error message", "code": "ERROR_CODE"}`

### HTTP Status Codes
- **200 OK**: Successful GET, PATCH requests
- **201 Created**: Successful POST request
- **204 No Content**: Successful DELETE request
- **401 Unauthorized**: Missing or invalid authentication
- **404 Not Found**: Resource doesn't exist
- **422 Unprocessable Entity**: Validation error
- **500 Internal Server Error**: Server error (logged, generic message to client)

### User Isolation Pattern
**CRITICAL**: Every query MUST filter by `user_id` to ensure data isolation

```python
# ❌ NEVER do this
async def get_tasks(session: Session):
    return session.exec(select(Task)).all()

# ✅ ALWAYS do this
async def get_tasks(session: Session, user_id: str):
    return session.exec(
        select(Task).where(Task.user_id == user_id)
    ).all()
```

### CORS Handling
- Configure allowed origins in environment variables
- Enable credentials for cookie-based auth
- Limit allowed methods to those actually used
- Cache preflight requests (max-age: 3600)

## Database Patterns

### SQLModel Type-Safe Queries
```python
from sqlmodel import select, Session
from src.models.task import Task

# ✅ Type-safe query with SQLModel
async def get_task(session: Session, task_id: str, user_id: str) -> Task | None:
    statement = select(Task).where(
        Task.id == task_id,
        Task.user_id == user_id  # ALWAYS filter by user_id
    )
    return session.exec(statement).first()
```

### Always Include user_id in WHERE Clauses
**This is a security requirement**, not optional:
- List queries: `WHERE user_id = :user_id`
- Get by ID: `WHERE id = :id AND user_id = :user_id`
- Update: `WHERE id = :id AND user_id = :user_id`
- Delete: `WHERE id = :id AND user_id = :user_id`

### Index Creation Guidelines
Create indexes for:
- Foreign keys (e.g., `task.user_id`)
- Frequently queried columns
- Composite indexes for common query patterns

```python
from sqlmodel import Field, SQLModel

class Task(SQLModel, table=True):
    id: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)  # Indexed!
    created_at: datetime = Field(index=True)  # Indexed for sorting
```

### Async Connection Pooling
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
)

async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

## Testing Requirements

### Coverage Target
- **Minimum**: 70% coverage
- **Measured By**: pytest-cov
- **Enforced**: `--cov-fail-under=70` in pyproject.toml

### TestClient for Endpoint Testing
```python
from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

def test_create_task():
    response = client.post(
        "/api/todos",
        json={"title": "Test Task"},
        headers={"Authorization": "Bearer mock-token"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Task"
```

### Mock JWT Verification
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.fixture
def mock_auth():
    with patch('src.auth.dependencies.verify_jwt') as mock:
        mock.return_value = {"sub": "user-123"}
        yield mock

def test_protected_endpoint(mock_auth):
    # Test runs with mocked authentication
    response = client.get("/api/todos")
    assert response.status_code == 200
```

### pytest Fixtures for Database Setup
```python
# tests/conftest.py
import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
```

## Error Handling

### Custom Exceptions for Domain Errors
```python
# src/exceptions/base.py
class TodoAppException(Exception):
    """Base exception for todo app"""
    pass

class TaskNotFoundError(TodoAppException):
    """Raised when task doesn't exist"""
    pass

class UnauthorizedError(TodoAppException):
    """Raised when user lacks permission"""
    pass
```

### Centralized Error Handlers
```python
# src/middleware/error_handler.py
from fastapi import Request, status
from fastapi.responses import JSONResponse

async def task_not_found_handler(request: Request, exc: TaskNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc), "code": "TASK_NOT_FOUND"}
    )

# Register in main.py
app.add_exception_handler(TaskNotFoundError, task_not_found_handler)
```

### Logging Strategy
- **Log 5xx errors**: Full stack trace, request details
- **Don't log 4xx errors**: Normal validation/auth failures
- **Return minimal details**: Don't expose internal errors to client

```python
import logging

logger = logging.getLogger(__name__)

try:
    result = dangerous_operation()
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise HTTPException(
        status_code=500,
        detail="Internal server error"  # Generic message
    )
```

### Validation Errors (422)
FastAPI handles Pydantic validation automatically:
```python
from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=2000)

# FastAPI returns 422 with field-level errors automatically
```

## Configuration Management

### Pydantic Settings
```python
# src/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    better_auth_url: str
    cors_origins: list[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
```

### Type-Safe Configuration Access
```python
# ✅ Type-safe, auto-completion works
from src.config import settings

db_url = settings.database_url  # str, checked by IDE

# ❌ Don't use os.getenv directly
import os
db_url = os.getenv("DATABASE_URL")  # str | None, no type safety
```

### Environment-Specific Overrides
```python
# .env (local development)
DATABASE_URL=sqlite:///./test.db
CORS_ORIGINS=["http://localhost:3000"]

# .env.production (production)
DATABASE_URL=postgresql://user:pass@host/db
CORS_ORIGINS=["https://app.example.com"]
```

## Security Best Practices

### JWT Verification via JWKS
```python
# src/auth/jwt_handler.py
import jwt
from jwt import PyJWKClient

jwks_client = PyJWKClient(f"{BETTER_AUTH_URL}/.well-known/jwks.json")

def verify_jwt(token: str) -> dict:
    signing_key = jwks_client.get_signing_key_from_jwt(token)
    return jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        audience="your-audience",
    )
```

### User Isolation Enforcement
Every CRUD function receives `user_id` and uses it in WHERE clause:
```python
def get_task(session: Session, task_id: str, user_id: str) -> Task | None:
    # Both id AND user_id required - prevents accessing other users' tasks
    return session.exec(
        select(Task).where(Task.id == task_id, Task.user_id == user_id)
    ).first()
```

### SQL Injection Prevention
SQLModel uses parameterized queries automatically:
```python
# ✅ Safe - SQLModel parameterizes
session.exec(select(Task).where(Task.title == user_input))

# ❌ NEVER do this - SQL injection risk
session.exec(f"SELECT * FROM task WHERE title = '{user_input}'")
```

### Rate Limiting Structure (Future-Proof)
```python
# Placeholder for future rate limiting
from fastapi import Request

async def rate_limit_middleware(request: Request, call_next):
    # TODO: Implement rate limiting
    response = await call_next(request)
    return response
```

## Common Patterns

### Creating New Endpoints
1. **Define route**: `src/routers/<resource>.py`
2. **Create schemas**: `src/schemas/<resource>.py` (Pydantic models)
3. **Implement CRUD**: `src/crud/<resource>.py` (business logic)
4. **Write tests**: `tests/integration/test_<resource>_api.py`
5. **Register router**: Add to `src/main.py`

Example:
```python
# src/routers/tasks.py
from fastapi import APIRouter, Depends
from src.schemas.task import TaskCreate, TaskRead
from src.crud.task import create_task
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/todos", tags=["tasks"])

@router.post("/", response_model=TaskRead, status_code=201)
async def create_task_endpoint(
    task_data: TaskCreate,
    user_id: str = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    return await create_task(session, task_data, user_id)
```

### Adding Database Models
1. **Create model**: `src/models/<resource>.py` (SQLModel)
2. **Add migration**: Create tables with `SQLModel.metadata.create_all()`
3. **Write tests**: `tests/unit/test_<resource>_model.py`

```python
# src/models/task.py
from sqlmodel import SQLModel, Field
from datetime import datetime
import uuid

class Task(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    title: str = Field(max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime | None = None
```

### Adding Authentication
Use dependency injection for protected endpoints:
```python
from fastapi import Depends
from src.auth.dependencies import get_current_user

@router.get("/protected")
async def protected_route(user_id: str = Depends(get_current_user)):
    # user_id extracted from JWT, guaranteed to be valid
    return {"message": f"Hello, user {user_id}"}
```

## What NOT to Do

### Security
- ❌ Don't skip `user_id` filtering in queries
- ❌ Don't return raw exceptions to client
- ❌ Don't use string concatenation for SQL
- ❌ Don't skip input validation
- ❌ Don't log sensitive data (passwords, tokens)

### Code Quality
- ❌ Don't use bare `except:` - catch specific exceptions
- ❌ Don't use mutable default arguments (`def func(items=[]):`)
- ❌ Don't ignore type hints - use mypy for validation
- ❌ Don't create unnecessary files or abstractions

### Database
- ❌ Don't fetch all records without pagination
- ❌ Don't run queries in loops (N+1 problem)
- ❌ Don't forget indexes on foreign keys
- ❌ Don't commit inside CRUD functions (let router handle it)

## Testing Patterns

### Unit Tests (CRUD Functions)
```python
# tests/unit/test_task_crud.py
import pytest
from src.crud.task import create_task
from src.schemas.task import TaskCreate

def test_create_task(session):
    task_data = TaskCreate(title="Test Task")
    user_id = "user-123"

    task = create_task(session, task_data, user_id)

    assert task.title == "Test Task"
    assert task.user_id == user_id
    assert task.completed is False
```

### Integration Tests (API Endpoints)
```python
# tests/integration/test_tasks_api.py
from fastapi.testclient import TestClient

def test_create_task_api(client: TestClient, mock_auth):
    response = client.post(
        "/api/todos",
        json={"title": "Test Task", "description": "Description"},
        headers={"Authorization": "Bearer mock-token"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert "id" in data
```

### Test User Isolation
```python
def test_user_cannot_access_other_tasks(client, mock_auth):
    # Create task as user-1
    mock_auth.return_value = {"sub": "user-1"}
    response = client.post("/api/todos", json={"title": "User 1 Task"})
    task_id = response.json()["id"]

    # Try to access as user-2
    mock_auth.return_value = {"sub": "user-2"}
    response = client.get(f"/api/todos/{task_id}")

    assert response.status_code == 404  # Not found (user-2 can't see it)
```

## Project Structure

```
src/
├── main.py                 # FastAPI app entry
├── config.py              # Pydantic Settings
├── db/
│   └── database.py        # Database connection
├── models/                # SQLModel entities
│   ├── user.py           # User model (read-only)
│   └── task.py           # Task model
├── schemas/               # Pydantic schemas
│   └── task.py           # Request/response models
├── auth/                  # Authentication
│   ├── jwt_handler.py    # JWT verification
│   └── dependencies.py   # Auth dependencies
├── crud/                  # Business logic
│   └── task.py           # Task CRUD operations
├── routers/               # API endpoints
│   ├── tasks.py          # Task endpoints
│   └── health.py         # Health check
├── middleware/            # Middleware
│   ├── cors.py           # CORS configuration
│   ├── error_handler.py  # Exception handling
│   └── logging.py        # Request logging
├── utils/                 # Utilities
│   ├── decorators.py     # Reusable decorators
│   └── constants.py      # Backend constants
└── exceptions/            # Custom exceptions
    ├── base.py           # Base exception classes
    └── handlers.py       # Exception handlers

tests/
├── conftest.py            # pytest fixtures
├── unit/                  # Unit tests
│   ├── test_task_model.py
│   └── test_task_crud.py
└── integration/           # Integration tests
    ├── test_tasks_api.py
    └── test_user_isolation.py
```

## Quick Commands

### Running Tests
```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_task_crud.py

# Run with markers
uv run pytest -m unit
uv run pytest -m integration
```

### Running the Server
```bash
# Development
uv run uvicorn src.main:app --reload

# Production
uv run uvicorn src.main:app --host 0.0.0.0 --port 8000
```

### Dependency Management
```bash
# Add package
uv add <package>

# Add dev package
uv add --dev <package>

# Update all packages
uv update
```

## Quick Reference

### Key Dependencies
- **Framework**: fastapi + uvicorn
- **ORM**: sqlmodel + sqlalchemy
- **Validation**: pydantic
- **Auth**: python-jose + passlib
- **Testing**: pytest + pytest-asyncio + httpx

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string
- `BETTER_AUTH_URL`: Better Auth server URL
- `CORS_ORIGINS`: Allowed CORS origins (JSON array)

### Response Models Pattern
```python
# Input: Creation/Update
class TaskCreate(BaseModel):
    title: str
    description: str | None = None

class TaskUpdate(BaseModel):
    title: str | None = None
    description: str | None = None

# Output: Response
class TaskRead(BaseModel):
    id: str
    title: str
    description: str | None
    completed: bool
    created_at: datetime

    class Config:
        from_attributes = True  # Allow SQLModel → Pydantic conversion
```

---

**Version**: 1.0.0
**Created**: 2026-01-17
**Updated**: 2026-01-17
**Related**: See root CLAUDE.md for project-wide standards
