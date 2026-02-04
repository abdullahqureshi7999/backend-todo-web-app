"""Integration tests for tasks API with tags functionality"""
import pytest


def test_api_create_task_with_tags(client, auth_headers):
    """Test POST /api/todos with tags"""
    response = client.post(
        "/api/todos",
        json={
            "title": "Task with tags",
            "description": "This has tags",
            "tags": ["work", "urgent", "important"]
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Task with tags"
    assert data["description"] == "This has tags"
    assert "tags" in data
    assert len(data["tags"]) == 3
    assert "work" in data["tags"]
    assert "urgent" in data["tags"]
    assert "important" in data["tags"]


def test_api_create_task_with_duplicate_tags(client, auth_headers):
    """Test POST /api/todos with duplicate tags (should deduplicate)"""
    response = client.post(
        "/api/todos",
        json={
            "title": "Task with duplicate tags",
            "tags": ["work", "work", "urgent", "work"]  # Multiple work tags
        },
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    # Should deduplicate tags
    assert len(data["tags"]) == 2  # Only "work" and "urgent"
    assert "work" in data["tags"]
    assert "urgent" in data["tags"]


def test_api_create_task_with_case_insensitive_tags(client, auth_headers):
    """Test POST /api/todos with case-insensitive tags"""
    # Create first task with tag in one case
    response1 = client.post(
        "/api/todos",
        json={
            "title": "Task with Work tag",
            "tags": ["Work"]  # Capital W
        },
        headers=auth_headers
    )
    assert response1.status_code == 201
    data1 = response1.json()

    # Create second task with same tag in different case
    response2 = client.post(
        "/api/todos",
        json={
            "title": "Task with WORK tag",
            "tags": ["WORK"]  # All caps
        },
        headers=auth_headers
    )
    assert response2.status_code == 201
    data2 = response2.json()

    # Both should have the same tag (normalized to lowercase)
    assert data1["tags"] == ["work"]
    assert data2["tags"] == ["work"]


def test_api_update_task_with_tags(client, auth_headers):
    """Test PATCH /api/todos/{id} with tags"""
    # Create initial task
    create_response = client.post(
        "/api/todos",
        json={
            "title": "Initial task",
            "tags": ["work"]
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    # Update tags
    update_response = client.patch(
        f"/api/todos/{task_id}",
        json={
            "tags": ["personal", "home"]
        },
        headers=auth_headers
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert len(data["tags"]) == 2
    assert "personal" in data["tags"]
    assert "home" in data["tags"]
    # Old tag should be gone
    assert "work" not in data["tags"]


def test_api_update_task_replace_all_tags(client, auth_headers):
    """Test that PATCH /api/todos/{id} replaces all tags when provided"""
    # Create task with multiple tags
    create_response = client.post(
        "/api/todos",
        json={
            "title": "Task with multiple tags",
            "tags": ["work", "urgent", "important"]
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    # Update with new tags (should replace all)
    update_response = client.patch(
        f"/api/todos/{task_id}",
        json={
            "tags": ["personal"]
        },
        headers=auth_headers
    )

    assert update_response.status_code == 200
    data = update_response.json()
    assert len(data["tags"]) == 1
    assert data["tags"] == ["personal"]


def test_api_get_task_includes_tags(client, auth_headers):
    """Test GET /api/todos/{id} includes tags in response"""
    # Create task with tags
    create_response = client.post(
        "/api/todos",
        json={
            "title": "Task with tags",
            "tags": ["work", "urgent"]
        },
        headers=auth_headers
    )
    assert create_response.status_code == 201
    task_id = create_response.json()["id"]

    # Get the task
    get_response = client.get(f"/api/todos/{task_id}", headers=auth_headers)
    assert get_response.status_code == 200
    data = get_response.json()

    assert data["id"] == task_id
    assert "tags" in data
    assert len(data["tags"]) == 2
    assert "work" in data["tags"]
    assert "urgent" in data["tags"]


def test_api_list_tasks_includes_tags(client, auth_headers):
    """Test GET /api/todos includes tags in response"""
    # Create tasks with tags
    client.post(
        "/api/todos",
        json={
            "title": "Task 1",
            "tags": ["work", "important"]
        },
        headers=auth_headers
    )
    client.post(
        "/api/todos",
        json={
            "title": "Task 2",
            "tags": ["personal"]
        },
        headers=auth_headers
    )

    # List tasks
    response = client.get("/api/todos", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data["tasks"]) == 2
    # Find each task and verify tags
    task1 = next(t for t in data["tasks"] if t["title"] == "Task 1")
    task2 = next(t for t in data["tasks"] if t["title"] == "Task 2")

    assert "work" in task1["tags"]
    assert "important" in task1["tags"]
    assert "personal" in task2["tags"]
