from __future__ import annotations

from project.domain.models.aggregates.webhook_delivery_attempt_aggregate import (
    WebhookDeliveryAttemptAggregate,
)
from project.extensions import db
from project.models.webhook_delivery_attempt_generated import (
    WebhookDeliveryAttemptGeneratedMixin,
)


class WebhookDeliveryAttempt(db.Model, WebhookDeliveryAttemptGeneratedMixin):
    @classmethod
    def from_aggregate(
        cls, aggregate: WebhookDeliveryAttemptAggregate
    ) -> WebhookDeliveryAttempt:
        model = cls()
        model.fill_from_aggregate(aggregate)
        return model

    def fill_from_aggregate(self, aggregate: WebhookDeliveryAttemptAggregate):
        self.id = aggregate.id if aggregate.id and aggregate.id > 0 else None
        self.url = aggregate.url
        self.start_at = aggregate.start_at
        self.end_at = aggregate.end_at
        self.webhook_delivery_id = aggregate.webhook_delivery_id
        self.status = aggregate.status
        self.status_code = aggregate.status_code

        return self

    @classmethod
    def to_aggregate(
        cls, model: WebhookDeliveryAttempt
    ) -> WebhookDeliveryAttemptAggregate:
        if model is None:  # pragma: no cover
            return None

        aggregate = WebhookDeliveryAttemptAggregate(
            id=model.id,
            url=model.url,
            start_at=model.start_at,
            end_at=model.end_at,
            webhook_delivery_id=model.webhook_delivery_id,
            status=model.status,
            status_code=model.status_code,
        )

        return aggregate
