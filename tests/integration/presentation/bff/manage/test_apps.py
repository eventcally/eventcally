import datetime
import hashlib

import pytest

BASE_URL = "/bff/manage/organizations/{}/apps"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/apps")


def _flashes(client):
    with client.session_transaction() as session:
        return [
            (category, str(message))
            for category, message in session.get("_flashes", [])
        ]


def _app_values(app, db, app_id):
    from project.infrastructure.models import OAuth2Client

    with app.app_context():
        client = db.session.get(OAuth2Client, app_id)
        return client and (
            client.client_name,
            client.scope,
            client.app_permissions,
            client.homepage_url,
            client.webhook and client.webhook.url,
        )


def _key_ids(app, db, app_id):
    from project.infrastructure.models import AppKey

    with app.app_context():
        return [
            k.id for k in db.session.query(AppKey).filter_by(oauth2_client_id=app_id)
        ]


def _delivery(app, db, app_id, event_type="app.installed"):
    from project.infrastructure.models.oauth import OAuth2Client
    from project.infrastructure.models.webhook import Webhook
    from project.infrastructure.models.webhook_delivery import WebhookDelivery
    from project.infrastructure.models.webhook_event import WebhookEvent

    with app.app_context():
        client = db.session.get(OAuth2Client, app_id)

        if client.webhook is None:
            webhook = Webhook()
            webhook.url = "https://example.test/webhook"
            webhook.secret = "test-secret"
            client.webhook = webhook
            db.session.add(webhook)
            db.session.flush()

        event = WebhookEvent()
        event.event_type = event_type
        event.timestamp = datetime.datetime.now(datetime.timezone.utc)
        event.payload = {}
        db.session.add(event)

        delivery = WebhookDelivery()
        delivery.app_id = app_id
        delivery.webhook = client.webhook
        delivery.webhook_event = event
        db.session.add(delivery)
        db.session.commit()
        return delivery.id


def _attempt(app, db, delivery_id):
    from project.infrastructure.models.webhook_delivery_attempt import (
        WebhookDeliveryAttempt,
    )

    with app.app_context():
        now = datetime.datetime.now(datetime.timezone.utc)
        attempt = WebhookDeliveryAttempt()
        attempt.webhook_delivery_id = delivery_id
        attempt.url = "https://example.test/webhook"
        attempt.status_code = "200"
        attempt.start_at = now
        attempt.end_at = now
        db.session.add(attempt)
        db.session.commit()
        return attempt.id


def _save_body(**kwargs):
    from project.presentation.shared.permissions import (
        organization_app_permission_infos,
    )
    from project.presentation.shared.scopes import scope_list

    body = dict(
        client_name="Meine App",
        redirect_uris=["https://example.test/cb", "  "],
        scopes=list(scope_list),
        app_permissions=[i.permission for i in organization_app_permission_infos],
        homepage_url="https://example.test",
        setup_url="https://example.test/setup",
        description="Eine App",
        webhook=dict(
            url="https://example.test/webhook",
            secret="geheim",
            disabled=False,
            event_types=["app.installed"],
        ),
    )
    body.update(kwargs)
    return body


@pytest.fixture
def setup(client, seeder, utils):
    # Webhook deliveries are not part of any organization role: platform admins only.
    user_id, admin_unit_id = seeder.setup_base(admin=True)
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    _shell(utils, admin_unit_id)
    return user_id, admin_unit_id, app_id


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    base = BASE_URL.format(admin_unit_id)
    body = _save_body()

    assert utils.get_json(base).status_code == 401
    assert utils.get_json(f"{base}/form").status_code == 401
    assert utils.get_json(f"{base}/1").status_code == 401
    assert utils.get_json(f"{base}/1/form").status_code == 401
    assert utils.post_json(base, body).status_code == 401
    assert utils.put_json(f"{base}/1", body).status_code == 401
    assert utils.post_json(f"{base}/1/delete", dict(name="x")).status_code == 401
    assert utils.post_json(f"{base}/1/keys", {}).status_code == 401
    assert utils.get_json(f"{base}/1/webhook-deliveries").status_code == 401
    assert (
        utils.post_json(f"{base}/1/webhook-deliveries/1/attempts", {}).status_code
        == 401
    )


def test_member_without_permission_is_403(client, app, db, seeder, utils):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    delivery_id = _delivery(app, db, app_id)
    utils.get_ok("/organizations")
    base = BASE_URL.format(admin_unit_id)
    body = _save_body()

    assert utils.get_json(base).status_code == 403
    assert utils.get_json(f"{base}/form").status_code == 403
    assert utils.get_json(f"{base}/{app_id}").status_code == 403
    assert utils.get_json(f"{base}/{app_id}/form").status_code == 403
    assert utils.post_json(base, body).status_code == 403
    assert utils.put_json(f"{base}/{app_id}", body).status_code == 403
    assert utils.post_json(f"{base}/{app_id}/delete", dict(name="x")).status_code == 403
    assert utils.post_json(f"{base}/{app_id}/keys", {}).status_code == 403
    assert (
        utils.post_json(f"{base}/{app_id}/keys/1/delete", dict(name="x")).status_code
        == 403
    )
    deliveries = f"{base}/{app_id}/webhook-deliveries"
    assert utils.get_json(deliveries).status_code == 403
    assert utils.get_json(f"{deliveries}/{delivery_id}").status_code == 403
    assert utils.get_json(f"{deliveries}/{delivery_id}/attempts").status_code == 403
    assert (
        utils.post_json(f"{deliveries}/{delivery_id}/attempts", {}).status_code == 403
    )


def test_writes_require_csrf(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    base = BASE_URL.format(admin_unit_id)

    assert utils.post_json(base, _save_body()).status_code == 400
    assert utils.put_json(f"{base}/{app_id}", _save_body()).status_code == 400
    assert utils.post_json(f"{base}/{app_id}/delete", dict(name="x")).status_code == 400
    assert utils.post_json(f"{base}/{app_id}/keys", {}).status_code == 400


def test_apps_of_others_are_404(client, app, db, seeder, utils, setup):
    user_id, admin_unit_id, _ = setup
    other_unit_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Andere Crew"
    )
    foreign_id = seeder.insert_default_oauth2_client_app(admin_unit_id=other_unit_id)
    foreign_key_id = seeder.insert_app_key(foreign_id)[1]
    foreign_delivery_id = _delivery(app, db, foreign_id)
    own_user_client_id = seeder.insert_default_oauth2_client(user_id=user_id)
    base = BASE_URL.format(admin_unit_id)

    for app_id in (foreign_id, own_user_client_id, 4711):
        assert utils.get_json(f"{base}/{app_id}").status_code == 404
        assert utils.get_json(f"{base}/{app_id}/form").status_code == 404
        assert utils.put_json(f"{base}/{app_id}", _save_body()).status_code == 404
        assert (
            utils.post_json(
                f"{base}/{app_id}/delete", dict(name="Mein Client")
            ).status_code
            == 404
        )
        assert utils.post_json(f"{base}/{app_id}/keys", {}).status_code == 404
        assert utils.get_json(f"{base}/{app_id}/webhook-deliveries").status_code == 404

    assert (
        utils.post_json(
            f"{base}/{foreign_id}/keys/{foreign_key_id}/delete", dict(name="x")
        ).status_code
        == 404
    )
    assert (
        utils.get_json(
            f"{base}/{foreign_id}/webhook-deliveries/{foreign_delivery_id}"
        ).status_code
        == 404
    )
    assert _app_values(app, db, foreign_id)[0] == "Mein Client"
    assert _key_ids(app, db, foreign_id) == [foreign_key_id]


def test_children_of_another_app_are_404(client, app, db, seeder, utils, setup):
    _, admin_unit_id, app_id = setup
    second_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    key_id = seeder.insert_app_key(second_id)[1]
    delivery_id = _delivery(app, db, second_id)
    base = BASE_URL.format(admin_unit_id)

    assert (
        utils.post_json(
            f"{base}/{app_id}/keys/{key_id}/delete", dict(name="x")
        ).status_code
        == 404
    )
    assert (
        utils.post_json(f"{base}/{app_id}/keys/4711/delete", dict(name="x")).status_code
        == 404
    )
    assert (
        utils.get_json(f"{base}/{app_id}/webhook-deliveries/{delivery_id}").status_code
        == 404
    )
    assert (
        utils.get_json(
            f"{base}/{app_id}/webhook-deliveries/{delivery_id}/attempts"
        ).status_code
        == 404
    )
    assert (
        utils.post_json(
            f"{base}/{app_id}/webhook-deliveries/{delivery_id}/attempts", {}
        ).status_code
        == 404
    )
    assert _key_ids(app, db, second_id) == [key_id]


# list, form, read


def test_list(client, seeder, utils, setup):
    user_id, admin_unit_id, app_id = setup
    seeder.insert_default_oauth2_client(admin_unit_id=admin_unit_id)

    body = utils.get_json_ok(BASE_URL.format(admin_unit_id)).json

    assert body["items"] == [dict(id=app_id, client_name="Mein Client")]
    assert body["total"] == 1
    assert body["can_write"] is True


def test_list_validates_the_query(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    url = BASE_URL.format(admin_unit_id)

    assert utils.get_json(url + "?per_page=0").status_code == 422
    assert utils.get_json(url + "?page=2").status_code == 404


def test_form_lists_the_choices(client, seeder, utils):
    from project.application.webhooks.app_webhooks import app_webhook_infos
    from project.presentation.shared.permissions import (
        organization_app_permission_infos,
    )
    from project.presentation.shared.scopes import scope_list

    _, admin_unit_id = seeder.setup_base()

    body = utils.get_json_ok(f"{BASE_URL.format(admin_unit_id)}/form").json

    assert body["scopes"] == scope_list
    assert [p["permission"] for p in body["app_permissions"]] == [
        i.permission for i in organization_app_permission_infos
    ]
    assert set(i.event_type for i in app_webhook_infos) <= set(body["event_types"])


def test_read_lists_the_keys(client, app, db, seeder, utils, setup):
    _, admin_unit_id, app_id = setup
    _, key_id = seeder.insert_app_key(app_id)
    base = BASE_URL.format(admin_unit_id)

    body = utils.get_json_ok(f"{base}/{app_id}").json

    assert body["client_name"] == "Mein Client"
    assert body["client_secret"]
    assert body["grant_types"]
    assert len(body["app_permissions"]) > 1
    assert body["webhook_url"] is None
    assert [k["id"] for k in body["keys"]] == [key_id]
    assert body["keys"][0]["kid"] and body["keys"][0]["checksum"]
    assert body["can_read_keys"] and body["can_write_keys"]
    assert body["can_read_deliveries"] and body["can_write"]
    assert "private_pem" not in str(body)


def test_organization_admin_does_not_see_webhook_deliveries(
    client, app, db, seeder, utils
):
    _, admin_unit_id = seeder.setup_base()
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)
    delivery_id = _delivery(app, db, app_id)
    base = f"{BASE_URL.format(admin_unit_id)}/{app_id}"

    body = utils.get_json_ok(base).json

    assert body["can_read_deliveries"] is False
    assert body["can_read_keys"] is True
    assert utils.get_json(f"{base}/webhook-deliveries").status_code == 403
    assert utils.get_json(f"{base}/webhook-deliveries/{delivery_id}").status_code == 403


def test_read_carries_the_audit(client, app, db, utils, setup):
    from sqlalchemy import text

    user_id, admin_unit_id, app_id = setup
    with app.app_context():
        db.session.execute(
            text(
                "UPDATE oauth2_client SET created_at = '2026-01-02 10:00',"
                " updated_at = '2026-01-03 11:00',"
                " created_by_id = :user_id, updated_by_id = :user_id WHERE id = :id"
            ),
            {"id": app_id, "user_id": user_id},
        )
        db.session.commit()

    audit = utils.get_json_ok(f"{BASE_URL.format(admin_unit_id)}/{app_id}").json[
        "audit"
    ]

    assert audit["created_by_label"] == "test@test.de"
    assert audit["updated_by_label"] == "test@test.de"
    assert audit["created_at"].startswith("2026-01-02T")
    assert audit["updated_at"].startswith("2026-01-03T")


def test_read_shows_the_webhook_url(client, app, db, seeder, utils, setup):
    _, admin_unit_id, app_id = setup
    _delivery(app, db, app_id)

    body = utils.get_json_ok(f"{BASE_URL.format(admin_unit_id)}/{app_id}").json

    assert body["webhook_url"] == "https://example.test/webhook"


def test_values_of_the_form(client, app, db, seeder, utils, setup):
    _, admin_unit_id, app_id = setup
    base = BASE_URL.format(admin_unit_id)

    body = utils.get_json_ok(f"{base}/{app_id}/form").json
    assert body["client_name"] == "Mein Client"
    assert body["webhook"] == dict(
        url=None, secret=None, disabled=False, event_types=[]
    )

    _delivery(app, db, app_id)
    body = utils.get_json_ok(f"{base}/{app_id}/form").json
    assert body["webhook"]["url"] == "https://example.test/webhook"
    assert body["webhook"]["secret"] == "test-secret"


# create, update, delete


def test_create(client, app, db, utils, setup):
    _, admin_unit_id, _ = setup

    response = utils.post_json(BASE_URL.format(admin_unit_id), _save_body())

    assert response.status_code == 201
    app_id = response.json["id"]
    assert response.json["redirect_url"].endswith(
        f"/manage/admin_unit/{admin_unit_id}/app/{app_id}"
    )
    name, scope, permissions, homepage, webhook_url = _app_values(app, db, app_id)
    assert name == "Meine App"
    assert scope
    assert permissions
    assert homepage == "https://example.test"
    assert webhook_url == "https://example.test/webhook"
    assert _flashes(client)[-1] == ("success", "App erfolgreich erstellt")


def test_create_without_webhook(client, app, db, utils, setup):
    _, admin_unit_id, _ = setup
    body = _save_body(webhook=dict(), homepage_url="", description="")

    response = utils.post_json(BASE_URL.format(admin_unit_id), body)

    assert response.status_code == 201
    assert _app_values(app, db, response.json["id"])[3:] == (None, None)


@pytest.mark.parametrize(
    "overrides, loc",
    [
        (dict(client_name=""), "client_name"),
        (dict(app_permissions=[]), "app_permissions"),
        (dict(app_permissions=["nope:read"]), "app_permissions"),
        (dict(scopes=["nope"]), "scopes"),
        (dict(webhook=dict(url="https://x.test", event_types=["nope"])), "webhook"),
        (dict(homepage_url="x" * 256), "homepage_url"),
    ],
)
def test_save_validates(client, utils, setup, overrides, loc):
    _, admin_unit_id, app_id = setup
    base = BASE_URL.format(admin_unit_id)

    for response in (
        utils.post_json(base, _save_body(**overrides)),
        utils.put_json(f"{base}/{app_id}", _save_body(**overrides)),
    ):
        assert response.status_code == 422
        assert response.json["errors"][0]["loc"][0] == loc


def test_update(client, app, db, utils, setup):
    _, admin_unit_id, app_id = setup
    body = _save_body(client_name="Neuer Name", webhook=dict())

    response = utils.put_json(f"{BASE_URL.format(admin_unit_id)}/{app_id}", body)

    assert response.status_code == 200
    assert response.json["id"] == app_id
    assert _app_values(app, db, app_id)[0] == "Neuer Name"
    assert _app_values(app, db, app_id)[4] is None
    assert _flashes(client)[-1] == ("success", "App erfolgreich aktualisiert")


def test_delete_requires_the_name(client, app, db, utils, setup):
    _, admin_unit_id, app_id = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{app_id}/delete", dict(name="Falscher Name")
    )

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["name"]
    assert _app_values(app, db, app_id) is not None


def test_delete_from_the_read_page_flashes(client, app, db, utils, setup):
    _, admin_unit_id, app_id = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{app_id}/delete", dict(name="mein client")
    )

    assert response.status_code == 200
    assert response.json["message"] == "App erfolgreich gelöscht"
    assert response.json["redirect_url"].endswith(
        f"/manage/admin_unit/{admin_unit_id}/apps"
    )
    assert _app_values(app, db, app_id) is None
    assert _flashes(client)[-1] == ("success", "App erfolgreich gelöscht")


def test_delete_from_the_list_does_not_flash(client, app, db, utils, setup):
    _, admin_unit_id, app_id = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{app_id}/delete",
        dict(name="Mein Client", inline=True),
    )

    assert response.status_code == 200
    assert _app_values(app, db, app_id) is None
    assert _flashes(client) == []


# keys


def test_create_key_answers_the_private_key_once(client, app, db, seeder, utils, setup):
    from cryptography.hazmat.primitives import serialization

    _, admin_unit_id, app_id = setup
    base = BASE_URL.format(admin_unit_id)

    response = utils.post_json(f"{base}/{app_id}/keys", {})

    assert response.status_code == 201
    assert response.headers["Cache-Control"] == "no-store"
    pem = response.json["private_pem"]
    serialization.load_pem_private_key(pem.encode("utf-8"), password=None)
    assert _key_ids(app, db, app_id) == [response.json["id"]]

    read = utils.get_json_ok(f"{base}/{app_id}")
    assert pem not in read.get_data(as_text=True)
    assert read.json["keys"] == [
        dict(
            id=response.json["id"],
            kid=response.json["kid"],
            checksum=hashlib.sha256(pem.encode("utf-8")).hexdigest(),
        )
    ]


def test_delete_key_requires_the_kid(client, app, db, seeder, utils, setup):
    _, admin_unit_id, app_id = setup
    _, key_id = seeder.insert_app_key(app_id)
    url = f"{BASE_URL.format(admin_unit_id)}/{app_id}/keys/{key_id}/delete"

    response = utils.post_json(url, dict(name="falsche-kid"))

    assert response.status_code == 422
    assert response.json["errors"][0]["loc"] == ["name"]
    assert _key_ids(app, db, app_id) == [key_id]


def test_delete_key(client, app, db, seeder, utils, setup):
    from project.infrastructure.models import AppKey

    _, admin_unit_id, app_id = setup
    _, key_id = seeder.insert_app_key(app_id)
    with app.app_context():
        kid = db.session.get(AppKey, key_id).kid
    url = f"{BASE_URL.format(admin_unit_id)}/{app_id}/keys/{key_id}/delete"

    response = utils.post_json(url, dict(name=kid, inline=True))

    assert response.status_code == 200
    assert response.json["message"] == "App key erfolgreich gelöscht"
    assert _key_ids(app, db, app_id) == []
    assert _flashes(client) == []

    _, second_id = seeder.insert_app_key(app_id)
    with app.app_context():
        kid = db.session.get(AppKey, second_id).kid
    utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{app_id}/keys/{second_id}/delete",
        dict(name=kid),
    )
    assert _flashes(client)[-1] == ("success", "App key erfolgreich gelöscht")


# webhook deliveries


def test_webhook_deliveries(client, app, db, utils, setup):
    _, admin_unit_id, app_id = setup
    delivery_id = _delivery(app, db, app_id)
    base = f"{BASE_URL.format(admin_unit_id)}/{app_id}/webhook-deliveries"

    page = utils.get_json_ok(base).json
    assert [i["id"] for i in page["items"]] == [delivery_id]
    assert page["items"][0]["event_type"] == "app.installed"
    assert page["total"] == 1
    assert page["app_title"] == "Mein Client"

    read = utils.get_json_ok(f"{base}/{delivery_id}").json
    assert read["id"] == delivery_id
    assert read["app_id"] == app_id
    assert read["app_title"] == "Mein Client"
    assert read["can_attempt"] is True
    assert read["organization"] is None

    assert utils.get_json(f"{base}/4711").status_code == 404
    assert utils.get_json(base + "?page=2").status_code == 404


def test_webhook_deliveries_name_the_installing_organization(
    client, app, db, seeder, utils, setup
):
    from project.infrastructure.models.webhook_delivery import WebhookDelivery

    _, admin_unit_id, app_id = setup
    delivery_id = _delivery(app, db, app_id)
    installation_id = seeder.install_app(app_id, admin_unit_id)
    with app.app_context():
        db.session.get(WebhookDelivery, delivery_id).app_installation_id = (
            installation_id
        )
        db.session.commit()

    page = utils.get_json_ok(
        f"{BASE_URL.format(admin_unit_id)}/{app_id}/webhook-deliveries"
    ).json

    assert page["items"][0]["organization"] == "Meine Crew"


def test_untitled_app_gets_a_fallback_title(client, app, db, utils, setup):
    from project.infrastructure.models import OAuth2Client

    _, admin_unit_id, app_id = setup
    delivery_id = _delivery(app, db, app_id)
    with app.app_context():
        db.session.get(OAuth2Client, app_id).set_client_metadata({})
        db.session.commit()

    read = utils.get_json_ok(
        f"{BASE_URL.format(admin_unit_id)}/{app_id}/webhook-deliveries/{delivery_id}"
    ).json

    assert read["app_title"].endswith(str(app_id))


def test_webhook_delivery_attempts(client, app, db, utils, setup):
    _, admin_unit_id, app_id = setup
    delivery_id = _delivery(app, db, app_id)
    attempt_id = _attempt(app, db, delivery_id)
    url = (
        f"{BASE_URL.format(admin_unit_id)}/{app_id}/webhook-deliveries/{delivery_id}"
        "/attempts"
    )

    page = utils.get_json_ok(url).json

    assert [i["id"] for i in page["items"]] == [attempt_id]
    assert page["items"][0]["status_code"] == "200"
    assert page["items"][0]["url"] == "https://example.test/webhook"
    assert page["can_write"] is True
    assert utils.get_json(url + "?page=2").status_code == 404


def test_deliver_again(client, app, db, utils, setup, mocker):
    from project.application.message_bus import MessageBus

    _, admin_unit_id, app_id = setup
    delivery_id = _delivery(app, db, app_id)
    dispatch = mocker.patch.object(MessageBus, "dispatch_command")
    url = (
        f"{BASE_URL.format(admin_unit_id)}/{app_id}/webhook-deliveries/{delivery_id}"
        "/attempts"
    )

    response = utils.post_json(url, {})

    assert response.status_code == 200
    assert response.json["message"] == "Webhook-Zustellversuch erfolgreich erstellt"
    command = dispatch.call_args.args[0]
    assert command.webhook_delivery_id == delivery_id


def test_app_of_an_organization_the_user_is_not_member_of_is_404(
    client, app, db, seeder, utils
):
    _, admin_unit_id = seeder.setup_base()
    other_unit_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Andere Crew"
    )
    foreign_id = seeder.insert_default_oauth2_client_app(admin_unit_id=other_unit_id)
    _shell(utils, admin_unit_id)
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(f"{base}/{foreign_id}").status_code == 404
    assert utils.put_json(f"{base}/{foreign_id}", _save_body()).status_code == 404
