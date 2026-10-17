from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.application.read_models.organization_ref_read_model import (
    OrganizationRefReadModel,
)
from project.domain.types.object_id import ObjectId


class CustomWidgetReadModel(BaseReadModel):
    """A custom widget as its API list/detail and the public widget loader show it."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    admin_unit_id: ObjectId
    widget_type: str
    name: str
    settings: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    admin_unit: OrganizationRefReadModel
