"""Base webhook payload data model."""

from typing import Optional

from project.application.webhooks.payloads.nested.payload_actor import PayloadActor
from project.domain.types.custom_base_model import CustomBaseModel


class WebhookPayloadBase(CustomBaseModel):
    actor: Optional[PayloadActor] = None
