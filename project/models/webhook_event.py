from __future__ import annotations

from project.domain.models.aggregates.webhook_event_aggregate import (
    WebhookEventAggregate,
)
from project.extensions import db
from project.models.webhook_event_generated import WebhookEventGeneratedMixin


class WebhookEvent(db.Model, WebhookEventGeneratedMixin):

    @classmethod
    def from_aggregate(cls, aggregate: WebhookEventAggregate) -> WebhookEvent:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: WebhookEventAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.timestamp = aggregate.timestamp
        self.event_type = aggregate.event_type
        self.payload = aggregate.payload

        return self

    @classmethod
    def to_aggregate(cls, model: WebhookEvent) -> WebhookEventAggregate:
        if model is None:  # pragma: no cover
            return None

        aggregate = WebhookEventAggregate(
            id=model.id,
            timestamp=model.timestamp,
            event_type=model.event_type,
            payload=model.payload,
        )

        return aggregate
