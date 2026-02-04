"""Unit tests for task CRUD operations with search functionality"""
import pytest
from sqlmodel import Session
from src.crud.task import create_task, list_tasks
from src.schemas.task import TaskCreate


def test_list_tasks_with_search_title(session: Session, mock_user_id: str):
    """Test searching tasks by title"""
    # Create tasks
    task1_data = TaskCreate(title="Meeting with client", description="Prepare presentation")
    task2_data = TaskCreate(title="Buy groceries", description="Milk and bread")
    task3_data = TaskCreate(title="Fix bug", description="Critical issue")

    create_task(session, task1_data, mock_user_id)
    create_task(session, task2_data, mock_user_id)
    create_task(session, task3_data, mock_user_id)

    # Search for "meeting"
    tasks = list_tasks(session, mock_user_id, search="meeting")
    assert len(tasks) == 1
    assert tasks[0].title == "Meeting with client"

    # Search for "bug"
    tasks = list_tasks(session, mock_user_id, search="bug")
    assert len(tasks) == 1
    assert tasks[0].title == "Fix bug"

    # Search for "critical"
    tasks = list_tasks(session, mock_user_id, search="critical")
    assert len(tasks) == 1
    assert tasks[0].title == "Fix bug"
    assert tasks[0].description == "Critical issue"


def test_list_tasks_with_search_case_insensitive(session: Session, mock_user_id: str):
    """Test that search is case insensitive"""
    task_data = TaskCreate(title="Important Meeting", description="Plan quarterly review")
    create_task(session, task_data, mock_user_id)

    # Search with different cases
    tasks = list_tasks(session, mock_user_id, search="important")
    assert len(tasks) == 1
    assert tasks[0].title == "Important Meeting"

    tasks = list_tasks(session, mock_user_id, search="MEETING")
    assert len(tasks) == 1
    assert tasks[0].title == "Important Meeting"


def test_list_tasks_with_search_partial_match(session: Session, mock_user_id: str):
    """Test that search works with partial matches"""
    task_data = TaskCreate(title="Weekly team meeting", description="Review progress")
    create_task(session, task_data, mock_user_id)

    # Search for partial matches
    tasks = list_tasks(session, mock_user_id, search="week")
    assert len(tasks) == 1
    assert tasks[0].title == "Weekly team meeting"

    tasks = list_tasks(session, mock_user_id, search="meet")
    assert len(tasks) == 1
    assert tasks[0].title == "Weekly team meeting"


def test_list_tasks_with_search_no_results(session: Session, mock_user_id: str):
    """Test search returns empty list when no matches"""
    task_data = TaskCreate(title="Meeting", description="Prepare agenda")
    create_task(session, task_data, mock_user_id)

    tasks = list_tasks(session, mock_user_id, search="nonexistent")
    assert len(tasks) == 0


def test_list_tasks_with_search_across_title_and_description(session: Session, mock_user_id: str):
    """Test search works across both title and description"""
    task1_data = TaskCreate(title="Marketing campaign", description="Not important")
    task2_data = TaskCreate(title="Bug fix", description="Critical marketing issue")
    task3_data = TaskCreate(title="Documentation", description="User guides")

    create_task(session, task1_data, mock_user_id)
    create_task(session, task2_data, mock_user_id)
    create_task(session, task3_data, mock_user_id)

    # Search for "marketing" - should match both title and description
    tasks = list_tasks(session, mock_user_id, search="marketing")
    assert len(tasks) == 2
    titles = [task.title for task in tasks]
    assert "Marketing campaign" in titles
    assert "Bug fix" in titles
