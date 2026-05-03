from typing import Any

from pydantic import Field

from project.domain.types import unset


def UnsetField(default: Any = unset, **kwargs):
    return Field(default=default, exclude_if=lambda v: v is unset, **kwargs)
