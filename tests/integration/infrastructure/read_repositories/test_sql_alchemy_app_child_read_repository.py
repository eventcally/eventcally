"""SqlAlchemyAppChildReadRepository against the database."""

import pytest

from project.application.queries import (
    ListAppKeysQuery,
    ListAppWebhookDeliveriesQuery,
    ListAppWebhookDeliveryAttemptsQuery,
)
from tests.integration.presentation.web.views.manage_admin_unit.test_webhook_delivery import (
    _create_webhook_delivery,
    _create_webhook_delivery_attempt,
)


@pytest.fixture
def read_repo(app, db):
    def call(method, *args, **kwargs):
        with app.app_context():
            repo = app.container.read_repos.app_child_read_repo()

            with app.container.infrastructure.read_session_scope():
                return getattr(repo, method)(*args, **kwargs)

    return call


def test_app_keys(read_repo, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    _, key_id = seeder.insert_app_key(app_id)

    page = read_repo("list_app_keys", ListAppKeysQuery(app_id=app_id))
    key = read_repo("get_app_key", key_id)

    assert [item.id for item in page.items] == [key_id]
    assert key.oauth2_client_id == app_id
    assert key.admin_unit_id == admin_unit_id
    assert key.kid and key.checksum
    assert read_repo("get_app_key", 4711) is None
    assert read_repo("app_admin_unit_id", app_id) == admin_unit_id
    assert read_repo("app_admin_unit_id", 4711) is None


def test_deliveries_and_attempts(app, db, read_repo, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    app_id, delivery_id = _create_webhook_delivery(app, db, seeder, admin_unit_id)
    attempt_id = _create_webhook_delivery_attempt(app, db, delivery_id)

    page = read_repo("list_deliveries", ListAppWebhookDeliveriesQuery(app_id=app_id))
    delivery = read_repo("get_delivery", delivery_id)
    attempts = read_repo(
        "list_attempts",
        ListAppWebhookDeliveryAttemptsQuery(webhook_delivery_id=delivery_id),
    )
    attempt = read_repo("get_attempt", attempt_id)

    assert [item.id for item in page.items] == [delivery_id]
    assert delivery.admin_unit_id == admin_unit_id
    assert delivery.app_id == app_id
    assert delivery.webhook_event.event_type == "app.installed"
    assert delivery.app_installation is None
    assert [item.id for item in attempts.items] == [attempt_id]
    assert attempt.status_code == "200"
    assert attempt.app_id == app_id
    assert attempt.admin_unit_id == admin_unit_id
    assert read_repo("webhook_delivery_admin_unit_id", delivery_id) == admin_unit_id
    assert read_repo("webhook_delivery_admin_unit_id", 4711) is None
    assert read_repo("get_delivery", 4711) is None
    assert read_repo("get_attempt", 4711) is None
