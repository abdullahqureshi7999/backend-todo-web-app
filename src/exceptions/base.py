"""Base exception classes for the todo application"""


class TodoAppException(Exception):
    """Base exception for all todo app exceptions"""
    pass


class TaskNotFoundError(TodoAppException):
    """Raised when a task is not found"""
    def __init__(self, task_id: str):
        self.task_id = task_id
        super().__init__(f"Task with id '{task_id}' not found")


class UnauthorizedError(TodoAppException):
    """Raised when a user is not authorized to perform an action"""
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message)


class ValidationError(TodoAppException):
    """Raised when validation fails"""
    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message)


class TagNotFoundError(TodoAppException):
    """Raised when a tag is not found"""
    def __init__(self, tag_id: str):
        self.tag_id = tag_id
        super().__init__(f"Tag with id '{tag_id}' not found")
