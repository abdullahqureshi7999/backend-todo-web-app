"""
Unit tests for User model

Reference: specs/001-todo-web-crud/spec.md
Task: T038 - Generate unit test for User model using /test-first-generator

Note: User model is read-only - managed by Better Auth, not by this application.
These tests verify the model structure matches Better Auth's schema.
"""
import pytest
from datetime import datetime, UTC
from src.models.user import User


class TestUserModel:
    """Test suite for User model structure and validation"""

    def test_create_user_with_all_fields(self):
        """Test creating a User instance with all required fields"""
        # Arrange
        user_data = {
            "id": "user-123",
            "email": "test@example.com",
            "name": "Test User",
            "emailVerified": True,
            "createdAt": datetime.now(UTC),
            "updatedAt": datetime.now(UTC),
        }

        # Act
        user = User(**user_data)

        # Assert
        assert user.id == user_data["id"]
        assert user.email == user_data["email"]
        assert user.name == user_data["name"]
        assert user.emailVerified == user_data["emailVerified"]
        assert isinstance(user.createdAt, datetime)
        assert isinstance(user.updatedAt, datetime)

    def test_user_email_is_unique_field(self):
        """Test that email field has unique constraint"""
        # Arrange - Access SQLModel table columns
        from sqlalchemy import inspect

        # Act - Get column information
        mapper = inspect(User)
        email_column = mapper.columns['email']

        # Assert - Check unique constraint and index
        assert email_column.unique is True, "Email should have unique constraint"
        assert email_column.index is True, "Email should be indexed"

    def test_user_email_verified_defaults_to_false(self):
        """Test that emailVerified defaults to False when not provided"""
        # Arrange & Act
        user = User(
            id="user-456",
            email="newuser@example.com",
            name="New User",
        )

        # Assert
        assert user.emailVerified is False

    def test_user_has_primary_key(self):
        """Test that User model has id as primary key"""
        # Arrange - Access SQLModel table columns
        from sqlalchemy import inspect

        # Act - Get column information
        mapper = inspect(User)
        id_column = mapper.columns['id']

        # Assert - Check primary key
        assert id_column.primary_key is True, "ID should be primary key"

    def test_user_timestamps_are_set(self):
        """Test that createdAt and updatedAt timestamps are properly set"""
        # Arrange
        before_create = datetime.now(UTC)

        # Act
        user = User(
            id="user-timestamp",
            email="timestamp@example.com",
            name="Timestamp User",
        )

        after_create = datetime.now(UTC)

        # Assert
        assert isinstance(user.createdAt, datetime)
        assert isinstance(user.updatedAt, datetime)
        assert before_create <= user.createdAt <= after_create
        assert before_create <= user.updatedAt <= after_create

    def test_user_model_has_all_required_fields(self):
        """Test that User model has all expected fields"""
        # Arrange
        expected_fields = {
            "id",
            "email",
            "name",
            "emailVerified",
            "createdAt",
            "updatedAt",
        }

        # Act
        actual_fields = set(User.model_fields.keys())

        # Assert
        assert expected_fields.issubset(actual_fields), \
            f"Missing fields: {expected_fields - actual_fields}"

    def test_user_model_table_name(self):
        """Test that User model maps to 'user' table"""
        # Act & Assert
        assert User.__tablename__ == "user"  # type: ignore

    @pytest.mark.parametrize("email", [
        "valid@example.com",
        "user.name@domain.co.uk",
        "test+tag@subdomain.example.com",
    ])
    def test_user_accepts_valid_email_formats(self, email: str):
        """Test that User model accepts various valid email formats"""
        # Arrange & Act
        user = User(
            id=f"user-{email}",
            email=email,
            name="Test User",
        )

        # Assert
        assert user.email == email
