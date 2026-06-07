from typing import Optional

from pydantic import ConfigDict

from project.application.read_models.base_read_model import BaseReadModel
from project.domain.types.object_id import ObjectId


class WebhookEventReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    event_type: str
    payload: dict


class WebhookReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    url: str
    secret: Optional[str] = None


class WebhookDeliveryReadModel(BaseReadModel):
    model_config = ConfigDict(frozen=True)

    id: ObjectId
    webhook_event: WebhookEventReadModel
    webhook: WebhookReadModel
    app_installation_id: Optional[ObjectId] = None
