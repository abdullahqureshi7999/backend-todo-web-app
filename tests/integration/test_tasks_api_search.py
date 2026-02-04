"""Integration tests for tasks API with search functionality"""
import pytest


def test_api_search_by_title(client, auth_headers):
    """Test GET /api/todos?search= works with title matching"""
    # Create tasks
    client.post(
        "/api/todos",
        json={"title": "Meeting with client", "description": "Prepare presentation"},
        headers=auth_headers
    )
    client.post(
        "/api/todos",
        json={"title": "Buy groceries", "description": "Milk and bread"},
        headers=auth_headers
    )
    client.post(
        "/api/todos",
        json={"title": "Fix critical bug", "description": "Production issue"},
        headers=auth_headers
    )

    # Search for "meeting"
    response = client.get("/api/todos?search=meeting", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert data["total"] == 3
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Meeting with client"

    # Search for "bug"
    response = client.get("/api/todos?search=bug", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Fix critical bug"


def test_api_search_by_description(client, auth_headers):
    """Test GET /api/todos?search= works with description matching"""
    client.post(
        "/api/todos",
        json={"title": "Task 1", "description": "Prepare for client meeting"},
        headers=auth_headers
    )
    client.post(
        "/api/todos",
        json={"title": "Task 2", "description": "Fix production bug"},
        headers=auth_headers
    )

    # Search for "client" in description
    response = client.get("/api/todos?search=client", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Task 1"

    # Search for "production" in description
    response = client.get("/api/todos?search=production", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Task 2"


def test_api_search_case_insensitive(client, auth_headers):
    """Test that search is case insensitive"""
    client.post(
        "/api/todos",
        json={"title": "Important Meeting", "description": "Plan quarterly review"},
        headers=auth_headers
    )

    # Search with lowercase
    response = client.get("/api/todos?search=important", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert data["tasks"][0]["title"] == "Important Meeting"

    # Search with uppercase
    response = client.get("/api/todos?search=MEETING", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert data["tasks"][0]["title"] == "Important Meeting"


def test_api_search_partial_match(client, auth_headers):
    """Test that search works with partial matches"""
    client.post(
        "/api/todos",
        json={"title": "Weekly team sync", "description": "Review progress"},
        headers=auth_headers
    )

    # Search for partial matches
    response = client.get("/api/todos?search=week", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert data["tasks"][0]["title"] == "Weekly team sync"

    response = client.get("/api/todos?search=sync", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 1
    assert data["tasks"][0]["title"] == "Weekly team sync"


def test_api_search_no_results(client, auth_headers):
    """Test search returns empty when no matches"""
    client.post(
        "/api/todos",
        json={"title": "Meeting", "description": "Prepare agenda"},
        headers=auth_headers
    )

    response = client.get("/api/todos?search=nonexistent", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 0
    assert len(data["tasks"]) == 0


def test_api_search_returns_counts(client, auth_headers):
    """Test that search endpoint returns correct total and filtered counts"""
    # Create 3 tasks
    client.post("/api/todos", json={"title": "Task 1"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Task 2"}, headers=auth_headers)
    client.post("/api/todos", json={"title": "Bug fix"}, headers=auth_headers)

    # Search for "bug"
    response = client.get("/api/todos?search=bug", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3  # Total tasks for user
    assert data["filtered"] == 1  # Filtered count
    assert len(data["tasks"]) == 1


def test_api_search_across_title_and_description(client, auth_headers):
    """Test search works across both title and description"""
    task1_data = {"title": "Marketing campaign", "description": "Not important"}
    task2_data = {"title": "Bug fix", "description": "Critical marketing issue"}
    task3_data = {"title": "Documentation", "description": "User guides"}

    client.post("/api/todos", json=task1_data, headers=auth_headers)
    client.post("/api/todos", json=task2_data, headers=auth_headers)
    client.post("/api/todos", json=task3_data, headers=auth_headers)

    # Search for "marketing" - should match both title and description
    response = client.get("/api/todos?search=marketing", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["filtered"] == 2
    titles = [task["title"] for task in data["tasks"]]
    assert "Marketing campaign" in titles
    assert "Bug fix" in titles


def test_api_search_with_special_characters(client, auth_headers):
    """Test search handles special characters safely"""
    client.post(
        "/api/todos",
        json={"title": "Task with special chars: @#$%", "description": "Test special chars"},
        headers=auth_headers
    )

    # Search for special characters
    response = client.get("/api/todos?search=@#$%", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    # Should not crash, but may not match depending on how search handles special chars
    # At minimum, should return valid JSON response
    assert "tasks" in data
    assert "total" in data
    assert "filtered" in data
