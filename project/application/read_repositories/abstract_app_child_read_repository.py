import abc
from typing import Optional

from project.application.queries.list_app_keys_query import ListAppKeysQuery
from project.application.queries.list_app_webhook_deliveries_query import (
    ListAppWebhookDeliveriesQuery,
)
from project.application.queries.list_app_webhook_delivery_attempts_query import (
    ListAppWebhookDeliveryAttemptsQuery,
)
from project.application.queries.list_webhook_deliveries_for_app_query import (
    ListWebhookDeliveriesForAppQuery,
)
from project.application.queries.list_webhook_delivery_attempts_for_app_query import (
    ListWebhookDeliveryAttemptsForAppQuery,
)
from project.application.read_models.app_child_read_models import (
    AppKeyReadModel,
    AppWebhookDeliveryAttemptReadModel,
    AppWebhookDeliveryReadModel,
)
from project.application.read_models.page import Page
from project.domain.types.object_id import ObjectId


class AbstractAppChildReadRepository(abc.ABC):
    """Resources below an app: keys, webhook deliveries and their attempts."""

    @abc.abstractmethod
    def app_admin_unit_id(
        self, app_id: ObjectId
    ) -> Optional[ObjectId]:  # pragma: no cover
        """The app's organization, or `None` if there is no such app."""
        raise NotImplementedError

    @abc.abstractmethod
    def webhook_delivery_admin_unit_id(
        self, webhook_delivery_id: ObjectId
    ) -> Optional[ObjectId]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_app_keys(
        self, query: ListAppKeysQuery
    ) -> Page[AppKeyReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_app_key(
        self, object_id: ObjectId
    ) -> Optional[AppKeyReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_deliveries(
        self, query: ListAppWebhookDeliveriesQuery
    ) -> Page[AppWebhookDeliveryReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_delivery(
        self, object_id: ObjectId
    ) -> Optional[AppWebhookDeliveryReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_attempts(
        self, query: ListAppWebhookDeliveryAttemptsQuery
    ) -> Page[AppWebhookDeliveryAttemptReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_attempt(
        self, object_id: ObjectId
    ) -> Optional[AppWebhookDeliveryAttemptReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_deliveries_for_app(
        self, query: ListWebhookDeliveriesForAppQuery
    ) -> Page[AppWebhookDeliveryReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def get_delivery_for_app(
        self, app_id: ObjectId, object_id: ObjectId
    ) -> Optional[AppWebhookDeliveryReadModel]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def list_attempts_for_app(
        self, query: ListWebhookDeliveryAttemptsForAppQuery
    ) -> Optional[Page[AppWebhookDeliveryAttemptReadModel]]:  # pragma: no cover
        """`None` unless the delivery belongs to `query.app_id`."""
        raise NotImplementedError
