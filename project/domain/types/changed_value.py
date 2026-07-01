from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class ChangedValue(BaseModel, Generic[T]):
    """Represents a value that has changed from an old value to a new value."""

    model_config = ConfigDict(frozen=True)

    old: T
    new: T


type ChangedOptionalValue[T] = ChangedValue[Optional[T]]
type OptionalChangedOptionalValue[T] = Optional[ChangedOptionalValue[T]]
type OptionalChangedValue[T] = Optional[ChangedValue[T]]
