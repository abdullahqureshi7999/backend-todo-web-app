"""Unit tests for task CRUD operations with tags"""
import pytest
from sqlmodel import Session
from src.crud.task import create_task, update_task
from src.schemas.task import TaskCreate, TaskUpdate


def test_create_task_with_tags(session: Session, mock_user_id: str):
    """Test creating a task with tags"""
    task_data = TaskCreate(
        title="Task with tags",
        description="This has tags",
        tags=["work", "urgent"]
    )

    task = create_task(session, task_data, mock_user_id)

    assert task.title == "Task with tags"
    assert task.description == "This has tags"
    assert len(task.tags) == 2
    tag_names = [tag.name for tag in task.tags]
    assert "work" in tag_names
    assert "urgent" in tag_names


def test_create_task_with_duplicate_tags(session: Session, mock_user_id: str):
    """Test creating a task with duplicate tags (should deduplicate)"""
    task_data = TaskCreate(
        title="Task with duplicate tags",
        tags=["work", "work", "urgent", "work"]  # Multiple work tags
    )

    task = create_task(session, task_data, mock_user_id)

    # Should have deduplicated tags
    assert len(task.tags) == 2  # Only "work" and "urgent"
    tag_names = [tag.name for tag in task.tags]
    assert "work" in tag_names
    assert "urgent" in tag_names


def test_update_task_with_tags(session: Session, mock_user_id: str):
    """Test updating a task's tags"""
    # Create initial task
    task_data = TaskCreate(
        title="Initial task",
        tags=["work"]
    )
    task = create_task(session, task_data, mock_user_id)

    # Update tags
    update_data = TaskUpdate(
        tags=["personal", "home"]
    )
    updated_task = update_task(session, task.id, update_data, mock_user_id)

    assert len(updated_task.tags) == 2
    tag_names = [tag.name for tag in updated_task.tags]
    assert "personal" in tag_names
    assert "home" in tag_names
    # Old tag should be removed
    assert "work" not in tag_names


def test_update_task_replace_all_tags(session: Session, mock_user_id: str):
    """Test that updating tags replaces all existing tags"""
    # Create task with multiple tags
    task_data = TaskCreate(
        title="Task with multiple tags",
        tags=["work", "urgent", "important"]
    )
    task = create_task(session, task_data, mock_user_id)

    assert len(task.tags) == 3

    # Update with new tags (should replace all)
    update_data = TaskUpdate(
        tags=["personal"]
    )
    updated_task = update_task(session, task.id, update_data, mock_user_id)

    assert len(updated_task.tags) == 1
    assert updated_task.tags[0].name == "personal"


def test_create_task_with_case_insensitive_tags(session: Session, mock_user_id: str):
    """Test that tags are case-insensitive and normalized"""
    # Create a tag in one case
    task_data = TaskCreate(
        title="Task with mixed case tag",
        tags=["WoRk"]  # Mixed case
    )
    task1 = create_task(session, task_data, mock_user_id)

    # Create another task with same tag in different case
    task_data2 = TaskCreate(
        title="Task with same tag different case",
        tags=["WORK"]  # Uppercase
    )
    task2 = create_task(session, task_data2, mock_user_id)

    # Both tasks should reference the same tag (lowercase)
    assert len(task1.tags) == 1
    assert len(task2.tags) == 1
    assert task1.tags[0].name == "work"
    assert task2.tags[0].name == "work"
    assert task1.tags[0].id == task2.tags[0].id  # Same tag object
