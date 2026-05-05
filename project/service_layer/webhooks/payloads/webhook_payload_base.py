"""Base webhook payload data model."""

from typing import Optional

from project.domain.types.custom_base_model import CustomBaseModel
from project.service_layer.webhooks.payloads.nested.actor import Actor


class WebhookPayloadBase(CustomBaseModel):
    actor: Optional[Actor] = None
