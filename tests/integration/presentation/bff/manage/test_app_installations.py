import pytest

BASE_URL = "/bff/manage/organizations/{}/app-installations"
INSTALLABLE_URL = "/bff/manage/organizations/{}/installable-apps/{}"


def _shell(utils, admin_unit_id):
    """Loads the Vue 3 shell: it carries the CSRF token for the writes."""
    utils.get_ok(f"/manage/admin_unit/{admin_unit_id}/app_installations")


def _flashes(client):
    with client.session_transaction() as session:
        return [
            (category, str(message))
            for category, message in session.get("_flashes", [])
        ]


def _installation_ids(app, db, admin_unit_id):
    from project.infrastructure.models import AppInstallation

    with app.app_context():
        return [
            i.id
            for i in db.session.query(AppInstallation).filter_by(
                admin_unit_id=admin_unit_id
            )
        ]


def _permissions(app, db, installation_id):
    from project.infrastructure.models import AppInstallation

    with app.app_context():
        return sorted(db.session.get(AppInstallation, installation_id).permissions)


def _app(app, db, seeder, admin_unit_id, **kwargs):
    app_id = seeder.insert_default_oauth2_client_app(admin_unit_id=admin_unit_id)

    with app.app_context():
        from project.infrastructure.models import OAuth2Client

        client = db.session.get(OAuth2Client, app_id)
        client.homepage_url = "https://example.com"
        client.description = "Eine App"

        for key, value in kwargs.items():
            setattr(client, key, value)

        db.session.commit()

    return app_id


@pytest.fixture
def setup(client, app, db, seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()
    other_unit_id = seeder.create_admin_unit(user_id, "Andere Crew")
    app_id = _app(app, db, seeder, other_unit_id)
    installation_id = seeder.install_app(app_id, admin_unit_id)
    _shell(utils, admin_unit_id)
    return admin_unit_id, other_unit_id, app_id, installation_id


# access


def test_anonymous_is_401(client, seeder, utils):
    owner_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(owner_id)
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(base).status_code == 401
    assert utils.get_json(f"{base}/1").status_code == 401
    assert utils.put_json(f"{base}/1/permissions").status_code == 401
    assert utils.post_json(f"{base}/1/delete", {}).status_code == 401
    assert utils.get_json(INSTALLABLE_URL.format(admin_unit_id, 1)).status_code == 401
    assert utils.post_json(base, dict(app_id=1)).status_code == 401


def test_member_without_permission_is_403(client, app, db, seeder, utils):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()
    app_id = _app(app, db, seeder, admin_unit_id)
    installation_id = seeder.install_app(app_id, admin_unit_id)
    utils.get_ok("/organizations")
    base = BASE_URL.format(admin_unit_id)

    assert utils.get_json(base).status_code == 403
    assert utils.get_json(f"{base}/{installation_id}").status_code == 403
    assert utils.put_json(f"{base}/{installation_id}/permissions").status_code == 403
    assert utils.post_json(f"{base}/{installation_id}/delete", {}).status_code == 403
    assert (
        utils.get_json(INSTALLABLE_URL.format(admin_unit_id, app_id)).status_code == 403
    )
    assert utils.post_json(base, dict(app_id=app_id)).status_code == 403


def test_writes_require_csrf(client, seeder, utils, app, db):
    _, admin_unit_id = seeder.setup_base()
    app_id = _app(app, db, seeder, admin_unit_id)
    installation_id = seeder.install_app(app_id, admin_unit_id)
    base = BASE_URL.format(admin_unit_id)

    assert utils.put_json(f"{base}/{installation_id}/permissions").status_code == 400
    assert utils.post_json(f"{base}/{installation_id}/delete", {}).status_code == 400
    assert utils.post_json(base, dict(app_id=app_id)).status_code == 400


def test_installations_of_others_are_404(client, app, db, seeder, utils, setup):
    admin_unit_id, other_unit_id, app_id, _ = setup
    foreign_id = seeder.install_app(app_id, other_unit_id)
    base = BASE_URL.format(admin_unit_id)

    for installation_id in (foreign_id, 4711):
        assert utils.get_json(f"{base}/{installation_id}").status_code == 404
        assert (
            utils.put_json(f"{base}/{installation_id}/permissions").status_code == 404
        )
        assert (
            utils.post_json(f"{base}/{installation_id}/delete", {}).status_code == 404
        )

    assert _installation_ids(app, db, other_unit_id) == [foreign_id]


# list and read


def test_list(client, utils, setup):
    admin_unit_id, _, _, installation_id = setup

    body = utils.get_json_ok(BASE_URL.format(admin_unit_id)).json

    assert [(i["id"], i["app"]) for i in body["items"]] == [
        (installation_id, "Mein Client")
    ]
    assert body["items"][0]["created_at"]
    assert body["total"] == 1
    assert body["can_write"] is True


def test_list_validates_the_query(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    url = BASE_URL.format(admin_unit_id)

    assert utils.get_json(url + "?per_page=0").status_code == 422
    assert utils.get_json(url + "?page=2").status_code == 404


def test_read(client, utils, setup):
    admin_unit_id, _, _, installation_id = setup

    body = utils.get_json_ok(f"{BASE_URL.format(admin_unit_id)}/{installation_id}").json

    assert body["app"] == "Mein Client"
    assert len(body["permissions"]) > 1
    assert body["requested_permissions"] == body["permissions"]
    assert body["needs_permission_update"] is False
    assert body["created_at"]
    assert body["can_write"] is True


def test_read_carries_the_audit(client, app, db, utils, setup):
    from sqlalchemy import text

    admin_unit_id, _, _, installation_id = setup
    with app.app_context():
        db.session.execute(
            text(
                "UPDATE app_installation SET created_at = '2026-01-02 10:00',"
                " created_by_id = 1 WHERE id = :id"
            ),
            {"id": installation_id},
        )
        db.session.commit()

    audit = utils.get_json_ok(
        f"{BASE_URL.format(admin_unit_id)}/{installation_id}"
    ).json["audit"]

    assert audit["created_by_label"] == "test@test.de"
    assert audit["created_at"].startswith("2026-01-02T")


def test_read_flags_permissions_the_app_requests_now(client, app, db, utils, setup):
    from project.infrastructure.models import AppInstallation

    admin_unit_id, _, _, installation_id = setup
    with app.app_context():
        db.session.get(AppInstallation, installation_id).permissions = ["events:read"]
        db.session.commit()

    body = utils.get_json_ok(f"{BASE_URL.format(admin_unit_id)}/{installation_id}").json

    assert len(body["permissions"]) == 1
    assert len(body["requested_permissions"]) > 1
    assert body["needs_permission_update"] is True


# accept permissions and uninstall


def test_accept_permissions(client, app, db, utils, setup):
    from project.infrastructure.models import AppInstallation, OAuth2Client

    admin_unit_id, _, app_id, installation_id = setup
    with app.app_context():
        db.session.get(AppInstallation, installation_id).permissions = ["events:read"]
        db.session.commit()
        requested = sorted(db.session.get(OAuth2Client, app_id).app_permissions)

    response = utils.put_json(
        f"{BASE_URL.format(admin_unit_id)}/{installation_id}/permissions"
    )

    assert response.status_code == 200
    assert response.json["message"] == "App installation erfolgreich aktualisiert"
    assert _permissions(app, db, installation_id) == requested


def test_uninstall_requires_no_name(client, app, db, utils, setup):
    admin_unit_id, _, _, installation_id = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{installation_id}/delete",
        dict(inline=True),
    )

    assert response.status_code == 200
    assert response.json["message"] == "App installation erfolgreich gelöscht"
    assert response.json["redirect_url"].endswith(
        f"/manage/admin_unit/{admin_unit_id}/app_installations"
    )
    assert _installation_ids(app, db, admin_unit_id) == []
    assert _flashes(client) == []


def test_uninstall_from_the_read_page_flashes(client, app, db, utils, setup):
    admin_unit_id, _, _, installation_id = setup

    response = utils.post_json(
        f"{BASE_URL.format(admin_unit_id)}/{installation_id}/delete", {}
    )

    assert response.status_code == 200
    assert _flashes(client)[-1] == ("success", "App installation erfolgreich gelöscht")


# install


def test_installable_app(client, utils, setup):
    admin_unit_id, _, app_id, _ = setup

    body = utils.get_json_ok(INSTALLABLE_URL.format(admin_unit_id, app_id)).json

    assert body["client_name"] == "Mein Client"
    assert body["homepage_url"] == "https://example.com"
    assert body["description"] == "Eine App"
    assert len(body["permissions"]) > 1
    assert (
        utils.get_json(INSTALLABLE_URL.format(admin_unit_id, 4711)).status_code == 404
    )


def test_install(client, app, db, seeder, utils, setup):
    admin_unit_id, other_unit_id, app_id, installation_id = setup
    seeder.create_admin_unit(seeder.create_user("dritter@test.de"), "Dritte Crew")
    target_id = other_unit_id

    response = utils.post_json(BASE_URL.format(target_id), dict(app_id=app_id))

    assert response.status_code == 201
    new_id = response.json["id"]
    assert response.json["redirect_url"].endswith(
        f"/manage/admin_unit/{target_id}/app_installation/{new_id}"
    )
    assert new_id in _installation_ids(app, db, target_id)
    assert _flashes(client)[-1] == ("success", "App successfully installed")


def test_install_flashes_the_setup_link(client, app, db, seeder, utils, setup):
    admin_unit_id, other_unit_id, app_id, _ = setup
    from project.infrastructure.models import OAuth2Client

    with app.app_context():
        db.session.get(OAuth2Client, app_id).setup_url = "https://example.com/setup"
        db.session.commit()

    response = utils.post_json(BASE_URL.format(other_unit_id), dict(app_id=app_id))

    assert response.status_code == 201
    category, message = _flashes(client)[-1]
    assert category == "success"
    assert message.startswith("App successfully installed")
    assert '<a href="https://example.com/setup">Setup</a>' in message


def test_install_unknown_app_is_404(client, utils, setup):
    admin_unit_id, _, _, _ = setup

    response = utils.post_json(BASE_URL.format(admin_unit_id), dict(app_id=4711))

    assert response.status_code == 404


def test_installation_of_an_organization_the_user_is_not_member_of_is_404(
    client, app, db, seeder, utils, setup
):
    admin_unit_id, _, app_id, _ = setup
    third_unit_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Dritte Crew"
    )
    foreign_id = seeder.install_app(app_id, third_unit_id)

    response = utils.get_json(f"{BASE_URL.format(admin_unit_id)}/{foreign_id}")

    assert response.status_code == 404
