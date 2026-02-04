"""Unit tests for task CRUD operations with filter functionality"""
import pytest
from sqlmodel import Session
from src.crud.task import create_task, list_tasks
from src.schemas.task import TaskCreate


def test_list_tasks_with_status_filter_pending(session: Session, mock_user_id: str):
    """Test filtering tasks by status - pending"""
    # Create tasks with different completion statuses
    task1_data = TaskCreate(title="Pending task 1", completed=False)
    task2_data = TaskCreate(title="Pending task 2", completed=False)
    task3_data = TaskCreate(title="Completed task", completed=True)

    create_task(session, task1_data, mock_user_id)
    create_task(session, task2_data, mock_user_id)
    create_task(session, task3_data, mock_user_id)

    # Filter for pending tasks
    tasks = list_tasks(session, mock_user_id, status="pending")
    assert len(tasks) == 2
    for task in tasks:
        assert task.completed is False


def test_list_tasks_with_status_filter_completed(session: Session, mock_user_id: str):
    """Test filtering tasks by status - completed"""
    # Create tasks with different completion statuses
    task1_data = TaskCreate(title="Completed task 1", completed=True)
    task2_data = TaskCreate(title="Completed task 2", completed=True)
    task3_data = TaskCreate(title="Pending task", completed=False)

    create_task(session, task1_data, mock_user_id)
    create_task(session, task2_data, mock_user_id)
    create_task(session, task3_data, mock_user_id)

    # Filter for completed tasks
    tasks = list_tasks(session, mock_user_id, status="completed")
    assert len(tasks) == 2
    for task in tasks:
        assert task.completed is True


def test_list_tasks_with_status_filter_all(session: Session, mock_user_id: str):
    """Test filtering tasks by status - all"""
    # Create tasks with different completion statuses
    task1_data = TaskCreate(title="Pending task", completed=False)
    task2_data = TaskCreate(title="Completed task", completed=True)

    create_task(session, task1_data, mock_user_id)
    create_task(session, task2_data, mock_user_id)

    # Filter for all tasks (default)
    tasks = list_tasks(session, mock_user_id, status="all")
    assert len(tasks) == 2


def test_list_tasks_with_priority_filter(session: Session, mock_user_id: str):
    """Test filtering tasks by priority"""
    # Create tasks with different priorities
    task1_data = TaskCreate(title="High priority", priority="high")
    task2_data = TaskCreate(title="Medium priority", priority="medium")
    task3_data = TaskCreate(title="Low priority", priority="low")
    task4_data = TaskCreate(title="No priority", priority="none")

    create_task(session, task1_data, mock_user_id)
    create_task(session, task2_data, mock_user_id)
    create_task(session, task3_data, mock_user_id)
    create_task(session, task4_data, mock_user_id)

    # Filter for high priority
    tasks = list_tasks(session, mock_user_id, priority="high")
    assert len(tasks) == 1
    assert tasks[0].title == "High priority"
    assert tasks[0].priority == "high"

    # Filter for medium priority
    tasks = list_tasks(session, mock_user_id, priority="medium")
    assert len(tasks) == 1
    assert tasks[0].title == "Medium priority"
    assert tasks[0].priority == "medium"


def test_list_tasks_with_tags_filter(session: Session, mock_user_id: str):
    """Test filtering tasks by tags"""
    # Create tasks with different tags
    task1_data = TaskCreate(title="Work task", tags=["work", "urgent"])
    task2_data = TaskCreate(title="Personal task", tags=["personal"])
    task3_data = TaskCreate(title="Home task", tags=["home", "personal"])

    create_task(session, task1_data, mock_user_id)
    create_task(session, task2_data, mock_user_id)
    create_task(session, task3_data, mock_user_id)

    # Filter for tasks with "work" tag
    tasks = list_tasks(session, mock_user_id, tags=["work"])
    assert len(tasks) == 1
    assert tasks[0].title == "Work task"

    # Filter for tasks with "personal" tag (should return 2 tasks)
    tasks = list_tasks(session, mock_user_id, tags=["personal"])
    assert len(tasks) == 2
    titles = [task.title for task in tasks]
    assert "Personal task" in titles
    assert "Home task" in titles


def test_list_tasks_with_no_tags_filter(session: Session, mock_user_id: str):
    """Test filtering tasks with no tags"""
    # Create tasks with and without tags
    task1_data = TaskCreate(title="Tagged task", tags=["work"])
    task2_data = TaskCreate(title="Untagged task", tags=[])
    task3_data = TaskCreate(title="Another untagged", tags=[])

    create_task(session, task1_data, mock_user_id)
    create_task(session, task2_data, mock_user_id)
    create_task(session, task3_data, mock_user_id)

    # Filter for tasks without tags
    tasks = list_tasks(session, mock_user_id, no_tags=True)
    assert len(tasks) == 2
    titles = [task.title for task in tasks]
    assert "Untagged task" in titles
    assert "Another untagged" in titles


def test_list_tasks_with_combined_filters(session: Session, mock_user_id: str):
    """Test combining multiple filters (AND logic)"""
    # Create tasks with different combinations
    task1_data = TaskCreate(title="High priority work", priority="high", tags=["work"], completed=False)
    task2_data = TaskCreate(title="Low priority work", priority="low", tags=["work"], completed=False)
    task3_data = TaskCreate(title="High priority personal", priority="high", tags=["personal"], completed=False)
    task4_data = TaskCreate(title="High priority completed", priority="high", tags=["work"], completed=True)

    create_task(session, task1_data, mock_user_id)
    create_task(session, task2_data, mock_user_id)
    create_task(session, task3_data, mock_user_id)
    create_task(session, task4_data, mock_user_id)

    # Filter for high priority AND work tag AND pending
    tasks = list_tasks(session, mock_user_id, priority="high", tags=["work"], status="pending")
    assert len(tasks) == 1
    assert tasks[0].title == "High priority work"
