"""Actor nested payload model."""

from typing import Optional

from project.application.webhooks.abstract_webhook_mapper_context import (
    AbstractWebhookMapperContext,
)
from project.domain.models.entities.actor import Actor as DomainActor
from project.domain.types.custom_base_model import CustomBaseModel


class PayloadActor(CustomBaseModel):
    user_id: Optional[int] = None
    app_installation_id: Optional[int] = None

    @classmethod
    def from_event(cls, actor: DomainActor, ctx: AbstractWebhookMapperContext):
        if actor is None:
            return None

        return cls(
            user_id=actor.user_id,
            app_installation_id=actor.app_installation_id,
        )
