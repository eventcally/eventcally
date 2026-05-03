from typing import Any

from pydantic import Field


def OptionalChangedValueField(default: Any = None, **kwargs):
    return Field(default=default, exclude_if=lambda v: v is None, **kwargs)
