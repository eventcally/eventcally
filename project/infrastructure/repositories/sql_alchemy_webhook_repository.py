import datetime

from project.domain.repositories.abstract_webhook_repository import (
    AbstractWebhookRepository,
)
from project.models.webhook_delivery import WebhookDelivery
from project.models.webhook_delivery_attempt import WebhookDeliveryAttempt
from project.models.webhook_event import WebhookEvent


class SqlAlchemyWebhookRepository(AbstractWebhookRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add_event(self, event: WebhookEvent):
        self.session.add(event)

    def _get_delivery(self, object_id: int):
        return self.session.query(WebhookDelivery).filter_by(id=object_id).first()

    def _get_delivery_attempt(self, object_id: int):
        return (
            self.session.query(WebhookDeliveryAttempt).filter_by(id=object_id).first()
        )

    def _delete_old_events(self, days: int) -> int:
        threshold_date = datetime.datetime.now(datetime.UTC) - datetime.timedelta(
            days=days
        )
        result = (
            self.session.query(WebhookEvent)
            .filter(WebhookEvent.timestamp < threshold_date)
            .delete(synchronize_session=False)
        )
        return result
