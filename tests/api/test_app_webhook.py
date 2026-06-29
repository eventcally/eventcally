import datetime

from tests.seeder import Seeder
from tests.utils import UtilActions


def _setup_app_auth(seeder: Seeder, utils: UtilActions, app, db, admin_unit_id):
    """Set up an app with auth key and return app_id, and webhook_delivery helper."""
    oauth2_client_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=admin_unit_id
    )
    private_pem, app_key_id = seeder.insert_app_key(oauth2_client_id)

    with app.app_context():
        from project.models import AppKey

        app_key = app.extensions["sqlalchemy"].session.get(AppKey, app_key_id)
        kid = app_key.kid

    utils.authorize_as_app(oauth2_client_id, private_pem, kid)
    return oauth2_client_id


def _create_webhook_delivery(app, db, oauth2_client_id):
    """Create a Webhook + WebhookEvent + WebhookDelivery for the given app and return delivery_id."""
    with app.app_context():
        from project.models import OAuth2Client
        from project.models.webhook import Webhook
        from project.models.webhook_delivery import WebhookDelivery
        from project.models.webhook_event import WebhookEvent

        session = app.extensions["sqlalchemy"].session

        # Associate a Webhook with the OAuth2Client
        oauth2_client = session.get(OAuth2Client, oauth2_client_id)
        if oauth2_client.webhook is None:
            webhook = Webhook()
            webhook.url = "https://example.test/webhook"
            webhook.event_types = ["app.installed"]
            session.add(webhook)
            session.flush()
            oauth2_client.webhook = webhook
            session.flush()

        webhook_event = WebhookEvent()
        webhook_event.event_type = "app.installed"
        webhook_event.timestamp = datetime.datetime.now(datetime.timezone.utc)
        webhook_event.payload = {}
        session.add(webhook_event)

        webhook_delivery = WebhookDelivery()
        webhook_delivery.app_id = oauth2_client_id
        webhook_delivery.webhook = oauth2_client.webhook
        webhook_delivery.webhook_event = webhook_event
        session.add(webhook_delivery)
        session.commit()

        return webhook_delivery.id


def test_app_webhook_delivery_list(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    oauth2_client_id = _setup_app_auth(seeder, utils, app, db, admin_unit_id)
    delivery_id = _create_webhook_delivery(app, db, oauth2_client_id)

    url = utils.get_url("api_v1_app_webhook_delivery_list")
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == delivery_id


def test_app_webhook_delivery_list_empty(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    _setup_app_auth(seeder, utils, app, db, admin_unit_id)

    url = utils.get_url("api_v1_app_webhook_delivery_list")
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 0


def test_app_webhook_delivery_read(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    oauth2_client_id = _setup_app_auth(seeder, utils, app, db, admin_unit_id)
    delivery_id = _create_webhook_delivery(app, db, oauth2_client_id)

    url = utils.get_url("api_v1_app_webhook_delivery", id=delivery_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert response.json["id"] == delivery_id


def test_app_webhook_delivery_attempt_list(
    client, app, db, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    oauth2_client_id = _setup_app_auth(seeder, utils, app, db, admin_unit_id)
    delivery_id = _create_webhook_delivery(app, db, oauth2_client_id)

    url = utils.get_url("api_v1_app_webhook_delivery_attempt_list", id=delivery_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 0


def test_app_webhook_delivery_attempt_trigger(
    client, app, db, seeder: Seeder, utils: UtilActions, requests_mock
):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    oauth2_client_id = _setup_app_auth(seeder, utils, app, db, admin_unit_id)
    delivery_id = _create_webhook_delivery(app, db, oauth2_client_id)

    url = utils.get_url("api_v1_app_webhook_delivery_attempt_list", id=delivery_id)
    response = utils.post_json(url, data={})
    assert response.status_code == 204


def test_app_webhook_schema_list(client, app, db, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    _setup_app_auth(seeder, utils, app, db, admin_unit_id)

    url = utils.get_url("api_v1_app_webhooks_schemas")
    response = utils.get_json(url)
    utils.assert_response_ok(response)
