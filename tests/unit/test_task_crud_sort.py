"""Unit tests for task CRUD operations with sort functionality"""
import pytest
from sqlmodel import Session
from src.crud.task import create_task, list_tasks
from src.schemas.task import TaskCreate


def test_list_tasks_with_title_sort_asc(session: Session, mock_user_id: str):
    """Test sorting tasks by title ascending"""
    # Create tasks in random order
    task_data = [
        TaskCreate(title="Zebra task", description="Last alphabetically"),
        TaskCreate(title="Alpha task", description="First alphabetically"),
        TaskCreate(title="Middle task", description="Middle alphabetically"),
    ]

    for data in task_data:
        create_task(session, data, mock_user_id)

    # Sort by title ascending
    tasks = list_tasks(session, mock_user_id, sort_field="title", sort_order="asc")
    assert len(tasks) == 3
    titles = [task.title for task in tasks]
    assert titles == ["Alpha task", "Middle task", "Zebra task"]


def test_list_tasks_with_title_sort_desc(session: Session, mock_user_id: str):
    """Test sorting tasks by title descending"""
    # Create tasks in random order
    task_data = [
        TaskCreate(title="Alpha task", description="First alphabetically"),
        TaskCreate(title="Middle task", description="Middle alphabetically"),
        TaskCreate(title="Zebra task", description="Last alphabetically"),
    ]

    for data in task_data:
        create_task(session, data, mock_user_id)

    # Sort by title descending
    tasks = list_tasks(session, mock_user_id, sort_field="title", sort_order="desc")
    assert len(tasks) == 3
    titles = [task.title for task in tasks]
    assert titles == ["Zebra task", "Middle task", "Alpha task"]


def test_list_tasks_with_created_at_sort_desc(session: Session, mock_user_id: str):
    """Test sorting tasks by creation date descending (newest first)"""
    # Create tasks in sequence (each will have slightly different timestamps)
    task1 = TaskCreate(title="First created", description="Created first")
    task2 = TaskCreate(title="Second created", description="Created second")
    task3 = TaskCreate(title="Third created", description="Created third")

    create_task(session, task1, mock_user_id)
    create_task(session, task2, mock_user_id)
    create_task(session, task3, mock_user_id)

    # Sort by created_at descending (newest first)
    tasks = list_tasks(session, mock_user_id, sort_field="created_at", sort_order="desc")
    assert len(tasks) == 3

    # Check that the order is newest first
    titles = [task.title for task in tasks]
    assert titles[0] == "Third created"  # Most recent
    assert titles[2] == "First created"  # Oldest


def test_list_tasks_with_created_at_sort_asc(session: Session, mock_user_id: str):
    """Test sorting tasks by creation date ascending (oldest first)"""
    # Create tasks in sequence (each will have slightly different timestamps)
    task1 = TaskCreate(title="First created", description="Created first")
    task2 = TaskCreate(title="Second created", description="Created second")
    task3 = TaskCreate(title="Third created", description="Created third")

    create_task(session, task1, mock_user_id)
    create_task(session, task2, mock_user_id)
    create_task(session, task3, mock_user_id)

    # Sort by created_at ascending (oldest first)
    tasks = list_tasks(session, mock_user_id, sort_field="created_at", sort_order="asc")
    assert len(tasks) == 3

    # Check that the order is oldest first
    titles = [task.title for task in tasks]
    assert titles[0] == "First created"  # Oldest
    assert titles[2] == "Third created"  # Most recent


def test_list_tasks_with_priority_sort(session: Session, mock_user_id: str):
    """Test sorting tasks by priority (high to low to none)"""
    # Create tasks with different priorities
    task_data = [
        TaskCreate(title="Low priority", priority="low"),
        TaskCreate(title="High priority", priority="high"),
        TaskCreate(title="None priority", priority="none"),
        TaskCreate(title="Medium priority", priority="medium"),
    ]

    for data in task_data:
        create_task(session, data, mock_user_id)

    # Sort by priority (default: high to low to none)
    tasks = list_tasks(session, mock_user_id, sort_field="priority", sort_order="asc")
    assert len(tasks) == 4

    # Check that the order is high -> medium -> low -> none
    priorities = [task.priority for task in tasks]
    assert priorities == ["high", "medium", "low", "none"]

    titles = [task.title for task in tasks]
    assert titles[0] == "High priority"
    assert titles[1] == "Medium priority"
    assert titles[2] == "Low priority"
    assert titles[3] == "None priority"


def test_list_tasks_default_sort_priority(session: Session, mock_user_id: str):
    """Test that default sort is by priority then creation date"""
    # Create tasks with mixed priorities and creation times
    task1 = TaskCreate(title="High priority first", priority="high")
    task2 = TaskCreate(title="Low priority second", priority="low")
    task3 = TaskCreate(title="High priority third", priority="high")
    task4 = TaskCreate(title="None priority fourth", priority="none")

    create_task(session, task1, mock_user_id)
    create_task(session, task2, mock_user_id)
    create_task(session, task3, mock_user_id)
    create_task(session, task4, mock_user_id)

    # Get tasks with default sort (priority asc, then created_at desc)
    tasks = list_tasks(session, mock_user_id)
    assert len(tasks) == 4

    # Should be sorted by priority first (high, medium, low, none)
    # Within same priority, should be sorted by created_at desc (newest first)
    priorities = [task.priority for task in tasks]
    assert priorities == ["high", "high", "low", "none"]  # High priority tasks first

    # The high priority tasks should be ordered by creation time (most recent first)
    high_priority_titles = [task.title for task in tasks if task.priority == "high"]
    assert high_priority_titles[0] == "High priority third"  # Created last
    assert high_priority_titles[1] == "High priority first"  # Created first
