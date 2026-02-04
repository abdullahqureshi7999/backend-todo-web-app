"""Integration tests for tags API endpoints"""
import pytest


def test_api_get_tags_empty(client, auth_headers):
    """Test GET /api/tags returns empty list when no tags exist"""
    response = client.get("/api/tags", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "tags" in data
    assert data["tags"] == []


def test_api_get_tags_with_tasks(client, auth_headers):
    """Test GET /api/tags returns tags with task counts"""
    # Create tasks with tags
    client.post(
        "/api/todos",
        json={
            "title": "Work task 1",
            "tags": ["work", "urgent"]
        },
        headers=auth_headers
    )
    client.post(
        "/api/todos",
        json={
            "title": "Work task 2",
            "tags": ["work"]  # Same tag, should increment count
        },
        headers=auth_headers
    )
    client.post(
        "/api/todos",
        json={
            "title": "Personal task",
            "tags": ["personal"]
        },
        headers=auth_headers
    )

    # Get tags
    response = client.get("/api/tags", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "tags" in data
    tags = data["tags"]
    assert len(tags) == 3  # work, urgent, personal

    # Find tags by name
    work_tag = next(tag for tag in tags if tag["name"] == "work")
    urgent_tag = next(tag for tag in tags if tag["name"] == "urgent")
    personal_tag = next(tag for tag in tags if tag["name"] == "personal")

    # Verify task counts
    assert work_tag["task_count"] == 2  # Used in 2 tasks
    assert urgent_tag["task_count"] == 1  # Used in 1 task
    assert personal_tag["task_count"] == 1  # Used in 1 task


def test_api_get_tags_case_insensitive_merge(client, auth_headers):
    """Test GET /api/tags shows case-insensitive tag merging"""
    # Create tasks with same tag in different cases
    client.post(
        "/api/todos",
        json={
            "title": "Task with Work tag",
            "tags": ["Work"]  # Capital W
        },
        headers=auth_headers
    )
    client.post(
        "/api/todos",
        json={
            "title": "Task with WORK tag",
            "tags": ["WORK"]  # All caps
        },
        headers=auth_headers
    )

    # Get tags - should show only one tag (merged)
    response = client.get("/api/tags", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    tags = data["tags"]
    assert len(tags) == 1  # Should be merged into one tag
    assert tags[0]["name"] == "work"  # Should be lowercase
    assert tags[0]["task_count"] == 2  # Should have 2 tasks


def test_api_get_tags_different_users_isolated(client, auth_headers, mock_auth):
    """Test GET /api/tags returns only tags for the authenticated user"""
    # Create task with tags for current user
    client.post(
        "/api/todos",
        json={
            "title": "User's work task",
            "tags": ["work", "urgent"]
        },
        headers=auth_headers
    )

    # Mock a different user
    mock_auth.return_value = {"sub": "other-user-id"}

    # Create task with tags for other user
    other_headers = {"Authorization": "Bearer mock-token"}
    client.post(
        "/api/todos",
        json={
            "title": "Other user's personal task",
            "tags": ["personal", "fun"]
        },
        headers=other_headers
    )

    # Current user should only see their tags
    response = client.get("/api/tags", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    tags = data["tags"]
    tag_names = [tag["name"] for tag in tags]
    assert "work" in tag_names
    assert "urgent" in tag_names
    assert "personal" not in tag_names  # Belongs to other user
    assert "fun" not in tag_names  # Belongs to other user


def test_api_get_tags_sorted_alphabetically(client, auth_headers):
    """Test GET /api/tags returns tags sorted alphabetically"""
    # Create tasks with tags in non-alphabetical order
    client.post(
        "/api/todos",
        json={
            "title": "Task with zebra tag",
            "tags": ["zebra"]
        },
        headers=auth_headers
    )
    client.post(
        "/api/todos",
        json={
            "title": "Task with alpha tag",
            "tags": ["alpha"]
        },
        headers=auth_headers
    )
    client.post(
        "/api/todos",
        json={
            "title": "Task with middle tag",
            "tags": ["middle"]
        },
        headers=auth_headers
    )

    # Get tags - should be sorted alphabetically
    response = client.get("/api/tags", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    tags = data["tags"]
    assert len(tags) == 3

    tag_names = [tag["name"] for tag in tags]
    assert tag_names == ["alpha", "middle", "zebra"]  # Should be alphabetical


def test_api_get_tags_with_special_characters(client, auth_headers):
    """Test GET /api/tags handles tags with special characters"""
    # Create tasks with tags that might have special characters
    client.post(
        "/api/todos",
        json={
            "title": "Task with special tag",
            "tags": ["web-dev", "ui_ux", "api_v2"]  # Using hyphens and underscores
        },
        headers=auth_headers
    )

    response = client.get("/api/tags", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    tags = data["tags"]
    tag_names = [tag["name"] for tag in tags]
    assert "web-dev" in tag_names
    assert "ui_ux" in tag_names
    assert "api_v2" in tag_names
