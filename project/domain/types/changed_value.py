from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ChangedValue(BaseModel, Generic[T]):
    """Represents a value that has changed from an old value to a new value."""

    model_config = ConfigDict(frozen=True)

    old: T
    new: T
