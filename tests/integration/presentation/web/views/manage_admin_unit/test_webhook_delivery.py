import datetime

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def _create_webhook_delivery(app, db, seeder, admin_unit_id):
    """Create an App with webhook, a WebhookDelivery, and return IDs."""
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    with app.app_context():
        from project.infrastructure.models.oauth import OAuth2Client
        from project.infrastructure.models.webhook import Webhook
        from project.infrastructure.models.webhook_delivery import WebhookDelivery
        from project.infrastructure.models.webhook_event import WebhookEvent

        oauth2_client = db.session.get(OAuth2Client, app_id)

        webhook = Webhook()
        webhook.url = "https://example.test/webhook"
        webhook.secret = "test-secret"
        oauth2_client.webhook = webhook
        db.session.add(webhook)
        db.session.flush()  # get webhook.id

        webhook_event = WebhookEvent()
        webhook_event.event_type = "app.installed"
        webhook_event.timestamp = datetime.datetime.now(datetime.timezone.utc)
        webhook_event.payload = {}
        db.session.add(webhook_event)

        webhook_delivery = WebhookDelivery()
        webhook_delivery.app_id = app_id
        webhook_delivery.webhook = webhook
        webhook_delivery.webhook_event = webhook_event
        db.session.add(webhook_delivery)
        db.session.commit()

        webhook_delivery_id = webhook_delivery.id
        webhook.id  # ensure loaded
        oauth2_client.id  # ensure loaded

    return app_id, webhook_delivery_id


def _create_webhook_delivery_attempt(app, db, webhook_delivery_id):
    """Create a WebhookDeliveryAttempt for the given delivery."""
    with app.app_context():
        from project.infrastructure.models.webhook_delivery_attempt import (
            WebhookDeliveryAttempt,
        )

        now = datetime.datetime.now(datetime.timezone.utc)
        attempt = WebhookDeliveryAttempt()
        attempt.webhook_delivery_id = webhook_delivery_id
        attempt.url = "https://example.test/webhook"
        attempt.status_code = "200"
        attempt.start_at = now
        attempt.end_at = now
        db.session.add(attempt)
        db.session.commit()
        return attempt.id


def test_list_and_read_are_shells(client, app, db, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()
    app_id, delivery_id = _create_webhook_delivery(app, db, seeder, admin_unit_id)

    response = utils.get_endpoint_ok(
        "manage_admin_unit.app.webhook_deliveries", id=admin_unit_id, app_id=app_id
    )
    utils.assert_response_contains(response, 'id="boot"')

    response = utils.get_endpoint_ok(
        "manage_admin_unit.app.webhook_delivery",
        id=admin_unit_id,
        app_id=app_id,
        webhook_delivery_id=delivery_id,
    )
    utils.assert_response_contains(response, 'id="boot"')


def test_delivery_of_another_app_is_unauthorized(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    _, admin_unit_id = seeder.setup_base()
    app_id, delivery_id = _create_webhook_delivery(app, db, seeder, admin_unit_id)
    other_app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.app.webhook_delivery",
            id=admin_unit_id,
            app_id=other_app_id,
            webhook_delivery_id=delivery_id,
        )
    )


def test_foreign_or_unknown_delivery(client, app, db, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    app_id, delivery_id = _create_webhook_delivery(app, db, seeder, admin_unit_id)
    other_admin_unit_id = seeder.create_admin_unit(user_id, "Other crew")

    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.app.webhook_delivery",
            id=other_admin_unit_id,
            app_id=app_id,
            webhook_delivery_id=delivery_id,
        )
    )
    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.app.webhook_delivery",
                id=admin_unit_id,
                app_id=app_id,
                webhook_delivery_id=4711,
            )
        )
    )


def test_removed_pages_are_gone(client, app, db, seeder: Seeder, utils: UtilActions):
    """The attempts are a section of the delivery page."""
    _, admin_unit_id = seeder.setup_base()
    app_id, delivery_id = _create_webhook_delivery(app, db, seeder, admin_unit_id)
    base = (
        f"/manage/admin_unit/{admin_unit_id}/app/{app_id}"
        f"/webhook_delivery/{delivery_id}"
    )

    for path in (
        "webhook_delivery_attempts",
        "webhook_delivery_attempt/create",
        "webhook_delivery_attempt/1",
    ):
        utils.assert_response_notFound(utils.get(f"{base}/{path}"))


def test_unknown_app_of_the_children_is_not_found(client, seeder: Seeder, utils):
    _, admin_unit_id = seeder.setup_base()

    utils.assert_response_notFound(
        utils.get(f"/manage/admin_unit/{admin_unit_id}/app/4711/webhook_deliveries")
    )


def test_member_without_admin_role_is_unauthorized(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member_event_verifier(admin_unit_id)
    utils.login()
    app_id, delivery_id = _create_webhook_delivery(app, db, seeder, admin_unit_id)

    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.app.webhook_deliveries",
            id=admin_unit_id,
            app_id=app_id,
        )
    )
    utils.get_unauthorized(
        utils.get_url(
            "manage_admin_unit.app.webhook_delivery",
            id=admin_unit_id,
            app_id=app_id,
            webhook_delivery_id=delivery_id,
        )
    )
