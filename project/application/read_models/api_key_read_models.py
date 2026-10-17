from datetime import datetime
from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.audit_read_model import AuditReadModel
from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class ApiKeyReadModel(BaseReadModel):
    """An API key as its list, read, update and delete pages show it. Implements the
    rate limit provider protocol `RateLimitProp` reads (key format of the ORM
    `RateLimitHolderMixin`)."""

    model_config = ConfigDict(frozen=True)

    id: ObjectId
    name: str
    admin_unit_id: Optional[ObjectId] = None
    user_id: Optional[ObjectId] = None
    rate_limit_value: str
    created_at: Optional[datetime] = None
    audit: Optional[AuditReadModel] = None  # get queries only

    def get_rate_limit_key(self) -> str:
        return f"apikey-{self.id}"

    def get_rate_limit_value(self) -> str:
        return self.rate_limit_value
