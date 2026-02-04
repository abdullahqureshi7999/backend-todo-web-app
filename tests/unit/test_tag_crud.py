"""Unit tests for tag CRUD operations"""
import pytest
from sqlmodel import Session
from src.crud.tag import get_or_create_tag, list_tags, get_tags_for_task, get_tag_stats
from src.schemas.task import TaskCreate
from src.crud.task import create_task


def test_get_or_create_tag_new(session: Session, mock_user_id: str):
    """Test getting or creating a new tag"""
    tag = get_or_create_tag(session, "work", mock_user_id)

    assert tag.name == "work"
    assert tag.user_id == mock_user_id

    # Verify it was saved to DB
    from src.models.tag import Tag
    from sqlmodel import select
    statement = select(Tag).where(
        Tag.name == "work",
        Tag.user_id == mock_user_id
    )
    db_tag = session.exec(statement).first()
    assert db_tag is not None
    assert db_tag.name == "work"


def test_get_or_create_tag_existing(session: Session, mock_user_id: str):
    """Test getting an existing tag (case-insensitive)"""
    # First create a tag
    tag1 = get_or_create_tag(session, "WORK", mock_user_id)
    assert tag1.name == "work"  # Should be lowercase

    # Try to create the same tag with different case
    tag2 = get_or_create_tag(session, "Work", mock_user_id)

    # Should return the same tag
    assert tag2.id == tag1.id
    assert tag2.name == "work"


def test_list_tags(session: Session, mock_user_id: str):
    """Test listing tags for a user"""
    # Create some tags
    get_or_create_tag(session, "work", mock_user_id)
    get_or_create_tag(session, "personal", mock_user_id)
    get_or_create_tag(session, "urgent", mock_user_id)

    tags = list_tags(session, mock_user_id)

    assert len(tags) == 3
    tag_names = [tag.name for tag in tags]
    assert "work" in tag_names
    assert "personal" in tag_names
    assert "urgent" in tag_names


def test_get_tag_stats(session: Session, mock_user_id: str):
    """Test getting tag statistics with task counts"""
    # Create a task with tags
    task_data = TaskCreate(
        title="Test task",
        tags=["work", "urgent"]
    )
    create_task(session, task_data, mock_user_id)

    stats = get_tag_stats(session, mock_user_id)

    # Should have stats for both tags
    stat_dict = {stat["name"]: stat["task_count"] for stat in stats}
    assert "work" in stat_dict
    assert "urgent" in stat_dict
    assert stat_dict["work"] == 1
    assert stat_dict["urgent"] == 1


def test_get_tags_for_task(session: Session, mock_user_id: str):
    """Test getting tags for a specific task"""
    # Create a task with tags
    task_data = TaskCreate(
        title="Test task",
        tags=["work", "personal"]
    )
    task = create_task(session, task_data, mock_user_id)

    # Get tags for the task
    from src.crud.tag import get_tags_for_task
    tags = get_tags_for_task(session, task.id, mock_user_id)

    assert len(tags) == 2
    tag_names = [tag.name for tag in tags]
    assert "work" in tag_names
    assert "personal" in tag_names
