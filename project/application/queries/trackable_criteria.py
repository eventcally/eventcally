from datetime import datetime
from enum import Enum
from typing import Optional

from project.domain.types.custom_base_model import CustomBaseModel


class TrackableCriteria(CustomBaseModel):
    """Optional created/updated/last-modified ranges: `_from` inclusive, `_to` exclusive."""

    created_at_from: Optional[datetime] = None
    created_at_to: Optional[datetime] = None
    updated_at_from: Optional[datetime] = None
    updated_at_to: Optional[datetime] = None
    last_modified_at_from: Optional[datetime] = None
    last_modified_at_to: Optional[datetime] = None


class TrackableSort(str, Enum):
    """The API `sort` values of `TrackableRequestSchemaMixin`."""

    created_at_desc = "-created_at"
    updated_at_desc = "-updated_at"
    last_modified_at_desc = "-last_modified_at"
