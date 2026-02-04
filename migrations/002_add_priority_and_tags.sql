-- Migration 002: Add priority and tags support
-- Created: 2026-01-23
-- Feature: 002-todo-organization-features

-- Step 1: Add priority column to task table
ALTER TABLE task ADD COLUMN priority VARCHAR(10) DEFAULT 'none';
CREATE INDEX idx_task_priority ON task(user_id, priority);

-- Step 2: Create tag table
CREATE TABLE tag (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) NOT NULL REFERENCES "user"(id),
    name VARCHAR(50) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE(user_id, name)
);
CREATE INDEX idx_tag_user_name ON tag(user_id, name);

-- Step 3: Create junction table for task-tag many-to-many relationship
CREATE TABLE task_tag (
    task_id VARCHAR(36) REFERENCES task(id) ON DELETE CASCADE,
    tag_id VARCHAR(36) REFERENCES tag(id) ON DELETE CASCADE,
    PRIMARY KEY (task_id, tag_id)
);
