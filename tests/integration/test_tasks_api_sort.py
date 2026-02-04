"""Integration tests for tasks API with sort functionality"""
import pytest


def test_api_sort_by_title_asc(client, auth_headers):
    """Test GET /api/todos?sort=title&order=asc"""
    # Create tasks in random order
    client.post("/api/todos", json={"title": "Zebra task", "description": "Last alphabetically"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Alpha task", "description": "First alphabetically"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Middle task", "description": "Middle alphabetically"}, headers=auth_headers)

    # Sort by title ascending
    response = client.get("/api/todos?sort=title&order=asc", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    titles = [task["title"] for task in data["tasks"]]
    assert titles == ["Alpha task", "Middle task", "Zebra task"]


def test_api_sort_by_title_desc(client, auth_headers):
    """Test GET /api/todos?sort=title&order=desc"""
    # Create tasks in random order
    client.post("/api/todos", json={"title": "Alpha task", "description": "First alphabetically"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Middle task", "description": "Middle alphabetically"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Zebra task", "description": "Last alphabetically"}, headers=auth_headers)

    # Sort by title descending
    response = client.get("/api/todos?sort=title&order=desc", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    titles = [task["title"] for task in data["tasks"]]
    assert titles == ["Zebra task", "Middle task", "Alpha task"]


def test_api_sort_by_created_at_desc(client, auth_headers):
    """Test GET /api/todos?sort=created_at&order=desc (newest first)"""
    # Create tasks in sequence (each will have slightly different timestamps)
    client.post("/api/todos", json={"title": "First created", "description": "Created first"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Second created", "description": "Created second"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Third created", "description": "Created third"}, headers=auth_headers)

    # Sort by created_at descending (newest first)
    response = client.get("/api/todos?sort=created_at&order=desc", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    titles = [task["title"] for task in data["tasks"]]
    assert titles[0] == "Third created"  # Most recent
    assert titles[-1] == "First created"  # Oldest


def test_api_sort_by_created_at_asc(client, auth_headers):
    """Test GET /api/todos?sort=created_at&order=asc (oldest first)"""
    # Create tasks in sequence (each will have slightly different timestamps)
    client.post("/api/todos", json={"title": "First created", "description": "Created first"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Second created", "description": "Created second"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Third created", "description": "Created third"}, headers=auth_headers)

    # Sort by created_at ascending (oldest first)
    response = client.get("/api/todos?sort=created_at&order=asc", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    titles = [task["title"] for task in data["tasks"]]
    assert titles[0] == "First created"  # Oldest
    assert titles[-1] == "Third created"  # Most recent


def test_api_sort_by_priority(client, auth_headers):
    """Test GET /api/todos?sort=priority&order=asc (high to low)"""
    # Create tasks with different priorities
    client.post("/api/todos", json={"title": "Low priority", "priority": "low"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "High priority", "priority": "high"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "None priority", "priority": "none"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Medium priority", "priority": "medium"}, headers=auth_headers)

    # Sort by priority ascending (high to low to none)
    response = client.get("/api/todos?sort=priority&order=asc", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    priorities = [task["priority"] for task in data["tasks"]]
    assert priorities == ["high", "medium", "low", "none"]

    titles = [task["title"] for task in data["tasks"]]
    assert titles[0] == "High priority"
    assert titles[1] == "Medium priority"
    assert titles[2] == "Low priority"
    assert titles[3] == "None priority"


def test_api_sort_default_priority(client, auth_headers):
    """Test that default sort is by priority (high to low to none)"""
    # Create tasks with different priorities
    client.post("/api/todos", json={"title": "Low priority", "priority": "low"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "High priority", "priority": "high"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "None priority", "priority": "none"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Medium priority", "priority": "medium"}, headers=auth_headers)

    # Get tasks with default sort
    response = client.get("/api/todos", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    priorities = [task["priority"] for task in data["tasks"]]
    assert priorities == ["high", "medium", "low", "none"]


def test_api_sort_with_filters(client, auth_headers):
    """Test that sort works together with filters"""
    # Create tasks with different attributes
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

    # Filter by work tag and sort by priority
    response = client.get("/api/todos?tags=work&sort=priority&order=asc", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 2  # Should return 2 work tasks
    titles = [task["title"] for task in data["tasks"]]
    assert titles[0] == "High priority work"  # High priority first
    assert titles[1] == "Low priority work"   # Then low priority


def test_api_sort_with_search(client, auth_headers):
    """Test that sort works together with search"""
    # Create tasks
    client.post("/api/todos", json={"title": "Fix high priority bug", "priority": "high"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Low priority documentation", "priority": "low"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Medium priority test", "priority": "medium"}, headers=auth_headers)

    # Search and sort simultaneously
    response = client.get("/api/todos?search=priority&sort=priority&order=asc", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # All titles should contain "priority"
    for task in data["tasks"]:
        assert "priority" in task["title"].lower()

    # Should be sorted by priority (high, medium, low)
    priorities = [task["priority"] for task in data["tasks"]]
    assert priorities == ["high", "medium", "low"]
