"""App key / webhook delivery query handlers — fake repository, no database."""

from datetime import datetime

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetAppKeyHandler,
    GetAppWebhookDeliveryAttemptHandler,
    GetAppWebhookDeliveryHandler,
    ListAppKeysHandler,
    ListAppWebhookDeliveriesHandler,
    ListAppWebhookDeliveryAttemptsHandler,
)
from project.application.read_models.app_child_read_models import (
    AppKeyReadModel,
    AppWebhookDeliveryAttemptReadModel,
    AppWebhookDeliveryReadModel,
    WebhookEventRefReadModel,
)
from project.application.read_models.page import Page
from project.application.read_repositories.abstract_app_child_read_repository import (
    AbstractAppChildReadRepository,
)
from project.domain.errors import UnauthorizedError
from tests.application.query_handlers.authz_helpers import ACTOR, authz

KEY = AppKeyReadModel(id=1, admin_unit_id=7, oauth2_client_id=3, kid="k", checksum="c")
DELIVERY = AppWebhookDeliveryReadModel(
    id=1,
    app_id=3,
    admin_unit_id=7,
    webhook_event=WebhookEventRefReadModel(event_type="app.installed"),
)
ATTEMPT = AppWebhookDeliveryAttemptReadModel(
    id=1,
    webhook_delivery_id=1,
    app_id=3,
    admin_unit_id=7,
    start_at=datetime(2026, 1, 1),
)


class FakeRepo(AbstractAppChildReadRepository):
    def app_admin_unit_id(self, app_id):
        return 7 if app_id == 3 else None

    def webhook_delivery_admin_unit_id(self, webhook_delivery_id):
        return 7 if webhook_delivery_id == 1 else None

    def _page(self, item):
        return Page(items=[item], page=1, per_page=20, total=1)

    def list_app_keys(self, query):
        return self._page(KEY)

    def get_app_key(self, object_id):
        return KEY if object_id == 1 else None

    def list_deliveries(self, query):
        return self._page(DELIVERY)

    def get_delivery(self, object_id):
        return DELIVERY if object_id == 1 else None

    def list_attempts(self, query):
        return self._page(ATTEMPT)

    def get_attempt(self, object_id):
        return ATTEMPT if object_id == 1 else None

    def list_deliveries_for_app(self, query):
        return self._page(DELIVERY)

    def get_delivery_for_app(self, app_id, object_id):
        return DELIVERY if (app_id, object_id) == (3, 1) else None

    def list_attempts_for_app(self, query):
        return self._page(ATTEMPT) if query.app_id == 3 else None


@pytest.mark.parametrize(
    "handler_class, query_class, parent, permission",
    [
        (ListAppKeysHandler, queries.ListAppKeysQuery, {"app_id": 3}, "app_keys:read"),
        (
            ListAppWebhookDeliveriesHandler,
            queries.ListAppWebhookDeliveriesQuery,
            {"app_id": 3},
            "webhook_deliveries:read",
        ),
        (
            ListAppWebhookDeliveryAttemptsHandler,
            queries.ListAppWebhookDeliveryAttemptsQuery,
            {"webhook_delivery_id": 1},
            "webhook_delivery_attempts:read",
        ),
    ],
)
def test_lists(handler_class, query_class, parent, permission):
    assert (
        handler_class(FakeRepo(), authz(permission))
        .handle(query_class(actor=ACTOR, **parent))
        .total
        == 1
    )

    missing = {key: 99 for key in parent}
    assert (
        handler_class(FakeRepo(), authz(permission)).handle(
            query_class(actor=ACTOR, **missing)
        )
        is None
    )

    with pytest.raises(UnauthorizedError):
        handler_class(FakeRepo(), authz()).handle(query_class(actor=ACTOR, **parent))


@pytest.mark.parametrize(
    "handler_class, query_class, permission, expected",
    [
        (GetAppKeyHandler, queries.GetAppKeyQuery, "app_keys:read", KEY),
        (
            GetAppWebhookDeliveryHandler,
            queries.GetAppWebhookDeliveryQuery,
            "webhook_deliveries:read",
            DELIVERY,
        ),
        (
            GetAppWebhookDeliveryAttemptHandler,
            queries.GetAppWebhookDeliveryAttemptQuery,
            "webhook_delivery_attempts:read",
            ATTEMPT,
        ),
    ],
)
def test_gets(handler_class, query_class, permission, expected):
    handler = handler_class(FakeRepo(), authz(permission))

    assert handler.handle(query_class(id=1, actor=ACTOR)) == expected
    assert handler.handle(query_class(id=2, actor=ACTOR)) is None

    with pytest.raises(UnauthorizedError):
        handler_class(FakeRepo(), authz()).handle(query_class(id=1, actor=ACTOR))


def test_app_scoped_queries_pass_through():
    from project.application.query_handlers import (
        GetWebhookDeliveryForAppHandler,
        ListWebhookDeliveriesForAppHandler,
        ListWebhookDeliveryAttemptsForAppHandler,
    )

    repo = FakeRepo()

    assert (
        ListWebhookDeliveriesForAppHandler(repo)
        .handle(queries.ListWebhookDeliveriesForAppQuery(app_id=3))
        .total
        == 1
    )
    assert (
        GetWebhookDeliveryForAppHandler(repo).handle(
            queries.GetWebhookDeliveryForAppQuery(app_id=3, id=1)
        )
        == DELIVERY
    )
    assert (
        GetWebhookDeliveryForAppHandler(repo).handle(
            queries.GetWebhookDeliveryForAppQuery(app_id=4, id=1)
        )
        is None
    )
    assert (
        ListWebhookDeliveryAttemptsForAppHandler(repo).handle(
            queries.ListWebhookDeliveryAttemptsForAppQuery(
                app_id=4, webhook_delivery_id=1
            )
        )
        is None
    )
