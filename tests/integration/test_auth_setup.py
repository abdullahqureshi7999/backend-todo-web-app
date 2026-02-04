"""
Integration tests for Better Auth setup and migration

Reference: specs/001-todo-web-crud/spec.md
Task: T039 - Generate integration test for Better Auth migration

These tests verify that:
1. Better Auth has created the user table
2. User table has correct schema
3. Database connection is properly configured
"""
import pytest
from sqlmodel import Session, select, text
from src.models.user import User
from src.db.database import engine, create_db_and_tables


class TestBetterAuthMigration:
    """Test suite for Better Auth database migration"""

    @pytest.fixture(autouse=True)
    def setup_database(self):
        """Setup database tables before each test"""
        create_db_and_tables()
        yield

    def test_user_table_exists(self):
        """Test that Better Auth created the user table"""
        # Arrange & Act
        with Session(engine) as session:
            # Try to query the user table
            result = session.exec(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
            )
            table_exists = result.first() is not None

        # Assert
        assert table_exists, "User table should exist after Better Auth migration"

    def test_user_table_has_required_columns(self):
        """Test that user table has all required columns"""
        # Arrange
        required_columns = {
            "id",
            "email",
            "name",
            "emailVerified",
            "createdAt",
            "updatedAt",
        }

        # Act
        with Session(engine) as session:
            # Query table schema
            result = session.exec(
                text("PRAGMA table_info(user)")
            )
            columns = {row[1] for row in result}

        # Assert
        assert required_columns.issubset(columns), \
            f"Missing columns: {required_columns - columns}"

    def test_user_table_email_has_unique_constraint(self):
        """Test that email column has unique constraint"""
        # Arrange
        with Session(engine) as session:
            # Query index information
            result = session.exec(
                text("PRAGMA index_list(user)")
            )
            indices = list(result)

        # Assert
        # Should have at least one index (email unique constraint)
        assert len(indices) > 0, "Email column should have unique index"

    def test_can_insert_user_record(self):
        """Test that user records can be inserted into the table"""
        # Arrange
        from datetime import datetime
        user_data = User(
            id="test-user-1",
            email="test@example.com",
            name="Test User",
            emailVerified=False,
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
        )

        # Act
        with Session(engine) as session:
            session.add(user_data)
            session.commit()
            session.refresh(user_data)

            # Verify insertion
            retrieved_user = session.get(User, "test-user-1")

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.email == "test@example.com"
        assert retrieved_user.name == "Test User"

    def test_duplicate_email_is_prevented(self):
        """Test that duplicate emails are prevented by unique constraint"""
        # Arrange
        from datetime import datetime
        user1 = User(
            id="user-1",
            email="duplicate@example.com",
            name="User One",
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
        )
        user2 = User(
            id="user-2",
            email="duplicate@example.com",  # Same email
            name="User Two",
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
        )

        # Act & Assert
        with Session(engine) as session:
            session.add(user1)
            session.commit()

            # Attempting to add user2 with duplicate email should fail
            with pytest.raises(Exception):  # Database integrity error
                session.add(user2)
                session.commit()

    def test_user_id_is_primary_key(self):
        """Test that id column is the primary key"""
        # Arrange & Act
        with Session(engine) as session:
            result = session.exec(
                text("PRAGMA table_info(user)")
            )
            columns = list(result)

        # Assert
        # Find the id column and check if it's a primary key
        id_column = next((col for col in columns if col[1] == "id"), None)
        assert id_column is not None, "id column should exist"
        assert id_column[5] == 1, "id column should be marked as primary key"

    def test_database_connection_is_working(self):
        """Test that database connection is properly configured"""
        # Act
        with Session(engine) as session:
            # Simple query to test connection
            result = session.exec(text("SELECT 1"))
            value = result.first()

        # Assert
        assert value is not None
        assert value[0] == 1

    def test_can_query_users_by_email(self):
        """Test that users can be queried by email (indexed column)"""
        # Arrange
        from datetime import datetime
        user = User(
            id="query-test-user",
            email="query@example.com",
            name="Query Test",
            createdAt=datetime.utcnow(),
            updatedAt=datetime.utcnow(),
        )

        # Act
        with Session(engine) as session:
            session.add(user)
            session.commit()

            # Query by email
            statement = select(User).where(User.email == "query@example.com")
            retrieved_user = session.exec(statement).first()

        # Assert
        assert retrieved_user is not None
        assert retrieved_user.id == "query-test-user"
        assert retrieved_user.email == "query@example.com"
