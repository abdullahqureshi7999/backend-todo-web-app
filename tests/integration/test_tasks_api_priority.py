"""Integration tests for tasks API with priority support"""
import pytest
from fastapi.testclient import TestClient
from src.models.priority import Priority


def test_create_task_with_priority(client: TestClient, auth_headers: dict):
    """Test POST /api/todos with priority"""
    response = client.post(
        "/api/todos",
        json={
            "title": "High priority task",
            "description": "This is urgent",
            "priority": "high",
            "tags": []
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "High priority task"
    assert data["priority"] == "high"
    assert "id" in data


def test_create_task_invalid_priority(client: TestClient, auth_headers: dict):
    """Test POST /api/todos with invalid priority returns 422"""
    response = client.post(
        "/api/todos",
        json={
            "title": "Task",
            "priority": "urgent"  # Invalid priority value
        },
        headers=auth_headers
    )

    assert response.status_code == 422


def test_get_todos_default_sort_by_priority(client: TestClient, auth_headers: dict):
    """Test GET /api/todos returns tasks sorted by priority by default"""
    # Create tasks with different priorities
    priorities = ["low", "high", "none", "medium"]
    for i, priority in enumerate(priorities):
        client.post(
            "/api/todos",
            json={"title": f"Task {i}", "priority": priority, "tags": []},
            headers=auth_headers
        )

    # Get all tasks
    response = client.get("/api/todos", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    tasks = data["tasks"]

    # Verify default sort order: high -> medium -> low -> none
    assert len(tasks) == 4
    assert tasks[0]["priority"] == "high"
    assert tasks[1]["priority"] == "medium"
    assert tasks[2]["priority"] == "low"
    assert tasks[3]["priority"] == "none"


def test_update_task_priority(client: TestClient, auth_headers: dict):
    """Test PATCH /api/todos/{id} can update priority"""
    # Create task
    create_response = client.post(
        "/api/todos",
        json={"title": "Task to update", "priority": "low", "tags": []},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]

    # Update priority
    update_response = client.patch(
        f"/api/todos/{task_id}",
        json={"priority": "high"},
        headers=auth_headers
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert data["priority"] == "high"
    assert data["title"] == "Task to update"  # Other fields unchanged


def test_get_task_includes_priority(client: TestClient, auth_headers: dict):
    """Test GET /api/todos/{id} includes priority in response"""
    # Create task
    create_response = client.post(
        "/api/todos",
        json={"title": "Task", "priority": "medium", "tags": []},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]

    # Get task
    get_response = client.get(f"/api/todos/{task_id}", headers=auth_headers)

    assert get_response.status_code == 200
    data = get_response.json()
    assert data["priority"] == "medium"
