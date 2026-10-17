"""Byte-level parity of the app API read endpoints (snapshot captured on the ORM
path, see `tests/integration/api/read_parity.py`)."""

import datetime

from tests.integration.api.read_parity import assert_matches_snapshot, set_trackable


def test_app_read_payloads_match_snapshot(app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base(admin=True, log_in=False)
    other_admin_unit_id = seeder.create_admin_unit(
        seeder.create_user("other@test.de"), "Andere Crew"
    )
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    other_app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    with app.app_context():
        from project.cli.seed_helpers import add_keypair_to_oauth2_client
        from project.models import OAuth2Client, Webhook, WebhookDelivery
        from project.models.webhook_delivery_attempt import WebhookDeliveryAttempt
        from project.models.webhook_event import WebhookEvent

        client = db.session.get(OAuth2Client, app_id)
        private_pem, app_key = add_keypair_to_oauth2_client(client)
        kid = app_key.kid
        db.session.commit()

    installations = [
        seeder.install_app(app_id, admin_unit_id),
        seeder.install_app(app_id, other_admin_unit_id),
    ]
    foreign_installation = seeder.install_app(other_app_id, other_admin_unit_id)

    with app.app_context():
        set_trackable(
            db,
            "app_installation",
            installations[0],
            datetime.datetime(2026, 1, 1, 10),
            datetime.datetime(2026, 3, 1, 12),
        )
        set_trackable(
            db,
            "app_installation",
            installations[1],
            datetime.datetime(2026, 2, 1, 9),
        )
        client = db.session.get(OAuth2Client, app_id)
        client.webhook = Webhook(url="https://hook.example.com", secret="s")
        db.session.flush()
        deliveries = []
        for i, (installation_id, timestamp) in enumerate(
            [
                (installations[0], datetime.datetime(2026, 1, 5, 8)),
                (None, datetime.datetime(2026, 1, 3, 8)),
                (installations[1], datetime.datetime(2026, 1, 4, 8)),
            ]
        ):
            event = WebhookEvent(
                event_type="app.installed", timestamp=timestamp, payload={"i": i}
            )
            delivery = WebhookDelivery(
                app_id=app_id,
                webhook=client.webhook,
                webhook_event=event,
                app_installation_id=installation_id,
            )
            db.session.add(delivery)
            db.session.flush()
            deliveries.append(delivery.id)

        for minute, status in [(1, "200"), (5, "500"), (3, "404")]:
            db.session.add(
                WebhookDeliveryAttempt(
                    webhook_delivery_id=deliveries[0],
                    url="https://hook.example.com",
                    status_code=status,
                    start_at=datetime.datetime(2026, 1, 6, 8, minute),
                    end_at=datetime.datetime(2026, 1, 6, 8, minute, 30),
                )
            )
        foreign_event = WebhookEvent(
            event_type="app.installed",
            timestamp=datetime.datetime(2026, 1, 1),
            payload={},
        )
        foreign_delivery = WebhookDelivery(
            app_id=other_app_id, webhook=client.webhook, webhook_event=foreign_event
        )
        db.session.add(foreign_delivery)
        db.session.commit()
        foreign_delivery_id = foreign_delivery.id

    utils.authorize_as_app(app_id, private_pem, kid)

    requests = {
        "installations": utils.get_url("api_v1_app_installation_list"),
        "installations_sort_updated_at": utils.get_url(
            "api_v1_app_installation_list", sort="-updated_at"
        ),
        "installations_created_at_from": utils.get_url(
            "api_v1_app_installation_list", created_at_from="2026-01-12T00:00:00"
        ),
        "installations_page_2": utils.get_url(
            "api_v1_app_installation_list", page=2, per_page=1
        ),
        "installation": utils.get_url("api_v1_app_installation", id=installations[1]),
        "installation_foreign": utils.get_url(
            "api_v1_app_installation", id=foreign_installation
        ),
        "deliveries": utils.get_url("api_v1_app_webhook_delivery_list"),
        "deliveries_page_2": utils.get_url(
            "api_v1_app_webhook_delivery_list", page=2, per_page=2
        ),
        "delivery": utils.get_url("api_v1_app_webhook_delivery", id=deliveries[0]),
        "delivery_without_installation": utils.get_url(
            "api_v1_app_webhook_delivery", id=deliveries[1]
        ),
        "delivery_foreign": utils.get_url(
            "api_v1_app_webhook_delivery", id=foreign_delivery_id
        ),
        "attempts": utils.get_url(
            "api_v1_app_webhook_delivery_attempt_list", id=deliveries[0]
        ),
        "attempts_page_2": utils.get_url(
            "api_v1_app_webhook_delivery_attempt_list",
            id=deliveries[0],
            page=2,
            per_page=2,
        ),
        "attempts_foreign": utils.get_url(
            "api_v1_app_webhook_delivery_attempt_list", id=foreign_delivery_id
        ),
    }

    assert_matches_snapshot("app", utils, requests)
