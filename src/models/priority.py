"""Priority enum for task prioritization."""
from enum import Enum


class Priority(str, Enum):
    """
    Task priority levels.

    Values are strings for JSON serialization and database storage.
    Sort order is defined separately for query optimization.
    """
    NONE = "none"      # Default, lowest sort priority
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# Sort order mapping (lower = higher priority in sort)
PRIORITY_SORT_ORDER = {
    Priority.HIGH: 0,
    Priority.MEDIUM: 1,
    Priority.LOW: 2,
    Priority.NONE: 3,
}
