import abc
from typing import Optional


class AbstractWebhookDeliverySender(abc.ABC):
    @abc.abstractmethod
    def send(
        self,
        *,
        url: str,
        secret: Optional[str],
        payload: dict,
        event_type: str,
        webhook_delivery_id: int,
        app_installation_id: Optional[int],
    ) -> tuple[str, Optional[str]]:  # pragma: no cover
        raise NotImplementedError
