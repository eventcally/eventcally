"""Parity of the app key and webhook delivery pages. Written against the ORM path
first."""

import datetime

from tests.views.manage_admin_unit.test_webhook_delivery import (
    _create_webhook_delivery,
    _create_webhook_delivery_attempt,
)


def _text(utils, response):
    return " ".join(utils.get_soup(response).get_text().split())


def _rows(utils, response):
    soup = utils.get_soup(response)
    return [" ".join(row.get_text().split()) for row in soup.select("table tbody tr")]


def test_app_key_pages(seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    other_app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    _, key_id = seeder.insert_app_key(app_id)
    seeder.insert_app_key(other_app_id)

    response = utils.get_ok(
        utils.get_url("manage_admin_unit.app.app_keys", id=admin_unit_id, app_id=app_id)
    )
    assert len(_rows(utils, response)) == 1

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.app.app_key",
            id=admin_unit_id,
            app_id=app_id,
            app_key_id=key_id,
        )
    )
    text = _text(utils, response)
    assert "Mein Client" in text
    assert f"App key {key_id}" in text

    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.app.app_key",
                id=admin_unit_id,
                app_id=other_app_id,
                app_key_id=key_id,
            )
        )
    )


def test_webhook_delivery_pages(app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_base(admin=True)
    app_id, delivery_id = _create_webhook_delivery(app, db, seeder, admin_unit_id)
    attempt_id = _create_webhook_delivery_attempt(app, db, delivery_id)

    with app.app_context():
        from project.models.webhook_delivery import WebhookDelivery
        from project.models.webhook_event import WebhookEvent

        event = WebhookEvent(
            event_type="app.uninstalled",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            payload={},
        )
        newer = WebhookDelivery(app_id=app_id, webhook_event=event)
        newer.webhook_id = db.session.get(WebhookDelivery, delivery_id).webhook_id
        db.session.add(newer)
        db.session.commit()

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.app.webhook_deliveries", id=admin_unit_id, app_id=app_id
        )
    )
    rows = _rows(utils, response)
    assert rows[0].startswith("app.uninstalled")
    assert rows[1].startswith("app.installed")

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.app.webhook_delivery",
            id=admin_unit_id,
            app_id=app_id,
            webhook_delivery_id=delivery_id,
        )
    )
    assert "app.installed" in _text(utils, response)

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.app.webhook_delivery.webhook_delivery_attempts",
            id=admin_unit_id,
            app_id=app_id,
            webhook_delivery_id=delivery_id,
        )
    )
    text = _text(utils, response)
    assert "https://example.test/webhook" in text
    assert f"Webhook-Zustellung {delivery_id}" in text

    response = utils.get_ok(
        utils.get_url(
            "manage_admin_unit.app.webhook_delivery.webhook_delivery_attempt",
            id=admin_unit_id,
            app_id=app_id,
            webhook_delivery_id=delivery_id,
            webhook_delivery_attempt_id=attempt_id,
        )
    )
    assert "200" in _text(utils, response)

    utils.assert_response_notFound(
        utils.get(
            utils.get_url(
                "manage_admin_unit.app.webhook_delivery.webhook_delivery_attempts",
                id=admin_unit_id,
                app_id=app_id,
                webhook_delivery_id=4711,
            )
        )
    )


def test_webhook_delivery_of_other_app(app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_base(admin=True)
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
