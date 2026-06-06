from __future__ import annotations

from project.application.read_models.webhook_delivery_read_model import (
    WebhookDeliveryReadModel,
    WebhookEventReadModel,
    WebhookReadModel,
)
from project.domain.models.aggregates.webhook_delivery_aggregate import (
    WebhookDeliveryAggregate,
)
from project.extensions import db
from project.models.webhook_delivery_generated import WebhookDeliveryGeneratedMixin


class WebhookDelivery(db.Model, WebhookDeliveryGeneratedMixin):
    @classmethod
    def from_aggregate(cls, aggregate: WebhookDeliveryAggregate) -> WebhookDelivery:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: WebhookDeliveryAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.webhook_event_id = aggregate.webhook_event_id
        self.webhook_id = aggregate.webhook_id
        self.app_installation_id = aggregate.app_installation_id
        self.app_id = aggregate.app_id

        return self

    @classmethod
    def to_aggregate(cls, model: WebhookDelivery) -> WebhookDeliveryAggregate:
        if model is None:  # pragma: no cover
            return None

        aggregate = WebhookDeliveryAggregate(
            id=model.id,
            webhook_event_id=model.webhook_event_id,
            webhook_id=model.webhook_id,
            app_installation_id=model.app_installation_id,
            app_id=model.app_id,
        )

        return aggregate

    @classmethod
    def to_read_model(cls, model: WebhookDelivery) -> WebhookDeliveryReadModel:
        if model is None:  # pragma: no cover
            return None

        return WebhookDeliveryReadModel(
            id=model.id,
            webhook_event=WebhookEventReadModel(
                event_type=model.webhook_event.event_type,
                payload=model.webhook_event.payload,
            ),
            webhook=WebhookReadModel(
                url=model.webhook.url, secret=model.webhook.secret
            ),
            app_installation_id=model.app_installation_id,
        )
