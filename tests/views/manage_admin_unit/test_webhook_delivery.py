import datetime

from tests.seeder import Seeder
from tests.utils import UtilActions


def _create_webhook_delivery(app, db, seeder, admin_unit_id):
    """Create an App with webhook, a WebhookDelivery, and return IDs."""
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    with app.app_context():
        from project.models.oauth import OAuth2Client
        from project.models.webhook import Webhook
        from project.models.webhook_delivery import WebhookDelivery
        from project.models.webhook_event import WebhookEvent

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
        from project.models.webhook_delivery_attempt import WebhookDeliveryAttempt

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


def test_webhook_delivery_list(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    app_id, webhook_delivery_id = _create_webhook_delivery(
        app, db, seeder, admin_unit_id
    )

    url = utils.get_url(
        "manage_admin_unit.app.webhook_deliveries",
        id=admin_unit_id,
        app_id=app_id,
    )
    utils.get_ok(url)


def test_webhook_delivery_read(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    app_id, webhook_delivery_id = _create_webhook_delivery(
        app, db, seeder, admin_unit_id
    )

    url = utils.get_url(
        "manage_admin_unit.app.webhook_delivery",
        id=admin_unit_id,
        app_id=app_id,
        webhook_delivery_id=webhook_delivery_id,
    )
    utils.get_ok(url)


def test_webhook_delivery_attempt_list(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    app_id, webhook_delivery_id = _create_webhook_delivery(
        app, db, seeder, admin_unit_id
    )

    url = utils.get_url(
        "manage_admin_unit.app.webhook_delivery.webhook_delivery_attempts",
        id=admin_unit_id,
        app_id=app_id,
        webhook_delivery_id=webhook_delivery_id,
    )
    utils.get_ok(url)


def test_webhook_delivery_attempt_create(
    client, app, db, seeder: Seeder, utils: UtilActions, requests_mock
):
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    app_id, webhook_delivery_id = _create_webhook_delivery(
        app, db, seeder, admin_unit_id
    )

    # mock the webhook delivery HTTP call
    requests_mock.post("https://example.test/webhook", status_code=200)

    url = utils.get_url(
        "manage_admin_unit.app.webhook_delivery.webhook_delivery_attempt_create",
        id=admin_unit_id,
        app_id=app_id,
        webhook_delivery_id=webhook_delivery_id,
    )
    response = utils.get_ok(url)
    # POST the form
    utils.post_form(url, response, {})


def test_webhook_delivery_attempt_read(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    """Read a specific delivery attempt – covers get_object_by_id and check_object_access."""
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    app_id, webhook_delivery_id = _create_webhook_delivery(
        app, db, seeder, admin_unit_id
    )
    attempt_id = _create_webhook_delivery_attempt(app, db, webhook_delivery_id)

    url = utils.get_url(
        "manage_admin_unit.app.webhook_delivery.webhook_delivery_attempt",
        id=admin_unit_id,
        app_id=app_id,
        webhook_delivery_id=webhook_delivery_id,
        webhook_delivery_attempt_id=attempt_id,
    )
    utils.get_ok(url)


def test_webhook_delivery_child_view_handler_check_object_access_abort(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    """Access an attempt via a different delivery URL – covers webhook_delivery/child_view_handler.py:25 abort."""
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    app_id, webhook_delivery_id_1 = _create_webhook_delivery(
        app, db, seeder, admin_unit_id
    )
    attempt_id = _create_webhook_delivery_attempt(app, db, webhook_delivery_id_1)

    # Create a second delivery for the SAME app
    with app.app_context():
        from project.models.webhook_delivery import WebhookDelivery
        from project.models.webhook_event import WebhookEvent

        webhook_event_2 = WebhookEvent()
        webhook_event_2.event_type = "app.installed"
        webhook_event_2.timestamp = datetime.datetime.now(datetime.timezone.utc)
        webhook_event_2.payload = {}
        db.session.add(webhook_event_2)

        from project.models.oauth import OAuth2Client

        oauth2_client = db.session.get(OAuth2Client, app_id)
        webhook_2 = oauth2_client.webhook

        webhook_delivery_2 = WebhookDelivery()
        webhook_delivery_2.app_id = app_id
        webhook_delivery_2.webhook = webhook_2
        webhook_delivery_2.webhook_event = webhook_event_2
        db.session.add(webhook_delivery_2)
        db.session.commit()
        webhook_delivery_id_2 = webhook_delivery_2.id

    # Access attempt of delivery_1 via delivery_2's URL – mismatch triggers abort(401)
    url = utils.get_url(
        "manage_admin_unit.app.webhook_delivery.webhook_delivery_attempt",
        id=admin_unit_id,
        app_id=app_id,
        webhook_delivery_id=webhook_delivery_id_2,  # wrong delivery
        webhook_delivery_attempt_id=attempt_id,
    )
    response = utils.get(url)
    assert response.status_code in (401, 403, 404)


def test_app_child_view_handler_check_object_access_abort(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    """Access a webhook delivery belonging to a different app – covers abort(401)."""
    user_id, admin_unit_id = seeder.setup_base(admin=True)

    # Create two apps; delivery belongs to app_id_1
    app_id_1, webhook_delivery_id = _create_webhook_delivery(
        app, db, seeder, admin_unit_id
    )
    app_id_2 = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    # Try to read delivery of app_1 using app_2's URL – should not return 200
    url = utils.get_url(
        "manage_admin_unit.app.webhook_delivery",
        id=admin_unit_id,
        app_id=app_id_2,  # wrong app
        webhook_delivery_id=webhook_delivery_id,
    )
    response = utils.get(url)
    assert response.status_code in (401, 403, 404)
