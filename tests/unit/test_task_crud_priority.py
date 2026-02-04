"""Unit tests for task CRUD operations with priority support"""
import pytest
from sqlmodel import Session, select
from src.crud.task import create_task, update_task, list_tasks
from src.schemas.task import TaskCreate, TaskUpdate
from src.models.task import Task
from src.models.priority import Priority


def test_create_task_with_priority(session: Session, mock_user_id: str):
    """Test creating a task with priority"""
    task_data = TaskCreate(
        title="High priority task",
        description="This is urgent",
        priority=Priority.HIGH,
        tags=[]
    )

    task = create_task(session, task_data, mock_user_id)

    assert task.priority == Priority.HIGH
    assert task.title == "High priority task"
    assert task.user_id == mock_user_id


def test_create_task_default_priority(session: Session, mock_user_id: str):
    """Test creating a task without specifying priority defaults to NONE"""
    task_data = TaskCreate(
        title="Task with default priority",
        tags=[]
    )

    task = create_task(session, task_data, mock_user_id)

    assert task.priority == Priority.NONE


def test_update_task_priority(session: Session, mock_user_id: str):
    """Test updating a task's priority"""
    # Create task with low priority
    task_data = TaskCreate(
        title="Task to update",
        priority=Priority.LOW,
        tags=[]
    )
    task = create_task(session, task_data, mock_user_id)

    # Update to high priority
    update_data = TaskUpdate(priority=Priority.HIGH)
    updated_task = update_task(session, task.id, update_data, mock_user_id)

    assert updated_task.priority == Priority.HIGH
    assert updated_task.title == "Task to update"  # Other fields unchanged


def test_list_tasks_sorted_by_priority(session: Session, mock_user_id: str):
    """Test listing tasks returns them sorted by priority (high to low)"""
    # Create tasks with different priorities
    priorities = [
        ("Low priority task", Priority.LOW),
        ("High priority task", Priority.HIGH),
        ("No priority task", Priority.NONE),
        ("Medium priority task", Priority.MEDIUM),
    ]

    for title, priority in priorities:
        task_data = TaskCreate(title=title, priority=priority, tags=[])
        create_task(session, task_data, mock_user_id)

    # List tasks
    tasks = list_tasks(session, mock_user_id)

    # Verify sort order: HIGH -> MEDIUM -> LOW -> NONE
    assert len(tasks) == 4
    assert tasks[0].priority == Priority.HIGH
    assert tasks[1].priority == Priority.MEDIUM
    assert tasks[2].priority == Priority.LOW
    assert tasks[3].priority == Priority.NONE


def test_list_tasks_priority_isolation(session: Session, mock_user_id: str, other_user_id: str):
    """Test that priority filtering respects user isolation"""
    # Create task for user 1
    task1 = TaskCreate(title="User 1 high task", priority=Priority.HIGH, tags=[])
    create_task(session, task1, mock_user_id)

    # Create task for user 2
    task2 = TaskCreate(title="User 2 high task", priority=Priority.HIGH, tags=[])
    create_task(session, task2, other_user_id)

    # User 1 should only see their task
    user1_tasks = list_tasks(session, mock_user_id)
    assert len(user1_tasks) == 1
    assert user1_tasks[0].title == "User 1 high task"

    # User 2 should only see their task
    user2_tasks = list_tasks(session, other_user_id)
    assert len(user2_tasks) == 1
    assert user2_tasks[0].title == "User 2 high task"
