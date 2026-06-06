import abc

from project.application.read_models.webhook_delivery_read_model import (
    WebhookDeliveryReadModel,
)


class AbstractWebhookDeliveryReadRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, object_id: int) -> WebhookDeliveryReadModel:  # pragma: no cover
        raise NotImplementedError
