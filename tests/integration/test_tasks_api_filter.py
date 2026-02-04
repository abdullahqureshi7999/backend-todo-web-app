"""Integration tests for tasks API with filter functionality"""
import pytest


def test_api_filter_by_status_pending(client, auth_headers):
    """Test GET /api/todos with status=pending"""
    # Create tasks with different statuses
    client.post("/api/todos", json={"title": "Pending task 1"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Pending task 2"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Completed task", "completed": True}, headers=auth_headers)

    # Filter for pending tasks
    response = client.get("/api/todos?status=pending", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 2
    assert len(data["tasks"]) == 2
    for task in data["tasks"]:
        assert task["completed"] is False


def test_api_filter_by_status_completed(client, auth_headers):
    """Test GET /api/todos with status=completed"""
    # Create tasks with different statuses
    client.post("/api/todos", json={"title": "Completed task 1", "completed": True}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Completed task 2", "completed": True}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Pending task"}, headers=auth_headers)

    # Filter for completed tasks
    response = client.get("/api/todos?status=completed", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 2
    assert len(data["tasks"]) == 2
    for task in data["tasks"]:
        assert task["completed"] is True


def test_api_filter_by_priority(client, auth_headers):
    """Test GET /api/todos with priority filter"""
    # Create tasks with different priorities
    client.post("/api/todos", json={"title": "High priority", "priority": "high"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Medium priority", "priority": "medium"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Low priority", "priority": "low"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "No priority", "priority": "none"}, headers=auth_headers)

    # Filter for high priority
    response = client.get("/api/todos?priority=high", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "High priority"
    assert data["tasks"][0]["priority"] == "high"

    # Filter for medium priority
    response = client.get("/api/todos?priority=medium", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Medium priority"


def test_api_filter_by_tags(client, auth_headers):
    """Test GET /api/todos with tags filter"""
    # Create tasks with different tags
    client.post("/api/todos", json={"title": "Work task", "tags": ["work", "urgent"]}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Personal task", "tags": ["personal"]}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Home task", "tags": ["home", "personal"]}, headers=auth_headers)

    # Filter for tasks with "work" tag
    response = client.get("/api/todos?tags=work", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Work task"

    # Filter for tasks with "personal" tag
    response = client.get("/api/todos?tags=personal", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 2  # Personal task and Home task
    assert len(data["tasks"]) == 2
    titles = [task["title"] for task in data["tasks"]]
    assert "Personal task" in titles
    assert "Home task" in titles


def test_api_filter_by_no_tags(client, auth_headers):
    """Test GET /api/todos with no_tags filter"""
    # Create tasks with and without tags
    client.post("/api/todos", json={"title": "Tagged task", "tags": ["work"]}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Untagged task", "tags": []}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Another untagged", "tags": []}, headers=auth_headers)

    # Filter for tasks without tags
    response = client.get("/api/todos?no_tags=true", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 2
    assert len(data["tasks"]) == 2
    titles = [task["title"] for task in data["tasks"]]
    assert "Untagged task" in titles
    assert "Another untagged" in titles


def test_api_combined_filters(client, auth_headers):
    """Test GET /api/todos with combined filters (AND logic)"""
    # Create tasks with different combinations
    client.post("/api/todos", json={
        "title": "High priority work",
        "priority": "high",
        "tags": ["work"],
        "completed": False
    }, headers=auth_headers)

    client.post("/api/todos", json={
        "title": "Low priority work",
        "priority": "low",
        "tags": ["work"],
        "completed": False
    }, headers=auth_headers)

    client.post("/api/todos", json={
        "title": "High priority personal",
        "priority": "high",
        "tags": ["personal"],
        "completed": False
    }, headers=auth_headers)

    client.post("/api/todos", json={
        "title": "High priority completed",
        "priority": "high",
        "tags": ["work"],
        "completed": True
    }, headers=auth_headers)

    # Filter for high priority AND work tag AND pending
    response = client.get("/api/todos?priority=high&tags=work&status=pending", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "High priority work"


def test_api_filter_returns_correct_counts(client, auth_headers):
    """Test that filter endpoint returns correct total and filtered counts"""
    # Create 4 tasks
    client.post("/api/todos", json={"title": "Task 1"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Task 2"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Task 3"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Task 4", "completed": True}, headers=auth_headers)

    # Filter for pending (should be 3)
    response = client.get("/api/todos?status=pending", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 4  # Total tasks
    assert data["filtered"] == 3  # Filtered count
    assert len(data["tasks"]) == 3


def test_api_filter_with_search(client, auth_headers):
    """Test combining search and filter parameters"""
    # Create tasks with different attributes
    client.post("/api/todos", json={
        "title": "Fix high priority bug",
        "priority": "high",
        "tags": ["work", "urgent"]
    }, headers=auth_headers)

    client.post("/api/todos", json={
        "title": "Low priority documentation",
        "priority": "low",
        "tags": ["work"]
    }, headers=auth_headers)

    client.post("/api/todos", json={
        "title": "Personal high priority task",
        "priority": "high",
        "tags": ["personal"]
    }, headers=auth_headers)

    # Combine search and filter
    response = client.get("/api/todos?search=bug&priority=high", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert len(data["tasks"]) == 1
    assert "bug" in data["tasks"][0]["title"].lower()
    assert data["tasks"][0]["priority"] == "high"
