"""pytest configuration and fixtures"""
import pytest
from typing import Generator
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Import all models to ensure they are registered with SQLModel before creating tables
from src.models.user import User  # noqa: F401
from src.models.task import Task  # noqa: F401
from src.models.tag import Tag, TaskTag  # noqa: F401


@pytest.fixture(name="engine")
def engine_fixture():
    """Create a test database engine"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine) -> Generator[Session, None, None]:
    """Create a test database session"""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session) -> Generator[TestClient, None, None]:
    """Create a test client"""
    from src.main import app
    from src.db.database import get_session

    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(name="mock_auth")
def mock_auth_fixture():
    """Mock JWT authentication"""
    with patch('src.auth.dependencies.verify_jwt') as mock:
        mock.return_value = {"sub": "test-user-id"}
        yield mock


@pytest.fixture(name="test_user_id")
def test_user_id_fixture() -> str:
    """Provide a test user ID"""
    return "test-user-id"


@pytest.fixture(name="mock_user_id")
def mock_user_id_fixture() -> str:
    """Provide a mock user ID for unit tests"""
    return "test-user-id"


@pytest.fixture(name="other_user_id")
def other_user_id_fixture() -> str:
    """Provide another user ID for isolation testing"""
    return "other-user-id"


@pytest.fixture(name="another_user_id")
def another_user_id_fixture() -> str:
    """Provide another test user ID for isolation testing"""
    return "another-user-id"


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(mock_auth) -> dict:
    """Provide authentication headers for API tests"""
    return {"Authorization": "Bearer mock-token"}
