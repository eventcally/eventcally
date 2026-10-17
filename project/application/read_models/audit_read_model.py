from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel


class AuditReadModel(BaseReadModel):
    """Who created/last updated an object and when, for the audit line under
    read/update displays. The labels are a user's email or an app's name."""

    model_config = ConfigDict(frozen=True)

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by_label: Optional[str] = None
    updated_by_label: Optional[str] = None
