import datetime

from project.domain.models.aggregates.webhook_event_aggregate import (
    WebhookEventAggregate,
)
from project.domain.repositories.abstract_webhook_event_repository import (
    AbstractWebhookEventRepository,
)
from project.models.webhook_event import WebhookEvent


class SqlAlchemyWebhookEventRepository(AbstractWebhookEventRepository):
    def __init__(self, session):
        super().__init__()
        self.session = session

    def _add(self, event: WebhookEventAggregate):
        model = WebhookEvent.from_aggregate(event)
        self.session.add(model)
        self.session.flush()

        event.id = model.id

    def _get(self, object_id: int) -> WebhookEventAggregate:
        model = self._get_model(object_id)
        return WebhookEvent.to_aggregate(model)

    def _get_model(self, object_id: int) -> WebhookEvent:
        return self.session.query(WebhookEvent).filter_by(id=object_id).first()

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
