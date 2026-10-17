from enum import Enum


class ApiKeySort(str, Enum):
    """Values equal the manage/user list sort keys."""

    name = "name"
    created_at_desc = "-created_at"
