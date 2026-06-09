"""Functions for mapping ChangedValue objects."""

from typing import Callable, List, Optional, TypeVar

from project.domain.types import ChangedValue

T = TypeVar("T")
U = TypeVar("U")


def map_changed_value(
    cv: Optional[ChangedValue[T]], converter: Callable[[T], U]
) -> Optional[ChangedValue[U]]:
    if cv is None:
        return None
    return ChangedValue(old=converter(cv.old), new=converter(cv.new))


def map_changed_list_value(
    cv: Optional[ChangedValue[List[T]]], converter: Callable[[T], U]
) -> Optional[ChangedValue[List[U]]]:
    if cv is None:  # pragma: no cover
        return None
    return ChangedValue(
        old=[converter(item) for item in cv.old],
        new=[converter(item) for item in cv.new],
    )


def map_list_value(values: List[T], converter: Callable[[T], U]) -> List[U]:
    return [converter(v) for v in values]
