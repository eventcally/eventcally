from typing import Optional

from project.domain.models.aggregates.webhook_delivery_attempt_aggregate import (
    WebhookDeliveryAttemptAggregate,
)
from project.domain.repositories.abstract_webhook_delivery_attempt_repository import (
    AbstractWebhookDeliveryAttemptRepository,
)
from project.models.webhook_delivery_attempt import WebhookDeliveryAttempt


class SqlAlchemyWebhookDeliveryAttemptRepository(
    AbstractWebhookDeliveryAttemptRepository
):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, attempt: WebhookDeliveryAttemptAggregate):
        model = WebhookDeliveryAttempt.from_aggregate(attempt)
        self.session.add(model)
        self.session.flush()

        attempt.id = model.id

    def _get_model(self, object_id: int) -> Optional[WebhookDeliveryAttempt]:
        return (
            self.session.query(WebhookDeliveryAttempt).filter_by(id=object_id).first()
        )

    def _get(self, object_id: int) -> Optional[WebhookDeliveryAttemptAggregate]:
        model = self._get_model(object_id)
        return WebhookDeliveryAttempt.to_aggregate(model)
