import pytest


def test_normal_user(client, seeder, utils):
    seeder.create_user()
    utils.login()
    response = client.get("/admin")
    assert response.status_code == 403


def test_admin_user(client, seeder, utils, app):
    seeder.create_user(admin=True)
    utils.login()
    response = client.get("/admin")
    assert response.status_code == 200


def test_admin_units(client, seeder, utils, app):
    seeder.create_user(admin=True)
    user = utils.login()
    seeder.create_admin_unit(user, "Meine Crew")
    response = client.get("/admin/admin_units")
    assert b"Meine Crew" in response.data


@pytest.mark.parametrize("db_error", [True, False])
def test_admin_settings(client, seeder, utils, app, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base(True)

    url = utils.get_url("admin_settings")
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "tos": "Meine Nutzungsbedingungen",
            "legal_notice": "Mein Impressum",
            "contact": "Mein Kontakt",
            "privacy": "Mein Datenschutz",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "admin")

    with app.app_context():
        from project.services.admin import upsert_settings

        settings = upsert_settings()
        assert settings.tos == "Meine Nutzungsbedingungen"
        assert settings.legal_notice == "Mein Impressum"
        assert settings.contact == "Mein Kontakt"
        assert settings.privacy == "Mein Datenschutz"


def test_admin_users(client, seeder, utils, app):
    seeder.create_user(admin=True)
    user = utils.login()
    seeder.create_admin_unit(user, "Meine Crew")
    response = client.get("/admin/users")
    assert b"test@test.de" in response.data


@pytest.mark.parametrize("db_error", [True, False])
def test_admin_user_update(client, seeder, utils, app, mocker, db, db_error):
    user_id, admin_unit_id = seeder.setup_base(True)
    other_user_id = seeder.create_user("other@test.de")

    with app.app_context():
        from project.models import User
        from project.services.user import set_roles_for_user

        user = User.query.get_or_404(other_user_id)
        set_roles_for_user(user.email, ["event_verifier"])
        db.session.commit()

    url = utils.get_url("admin_user_update", id=other_user_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "roles": "admin",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "admin_users")

    with app.app_context():
        from project.models import User

        user = User.query.get_or_404(other_user_id)
        assert len(user.roles) == 1
        assert any(r.name == "admin" for r in user.roles)


@pytest.mark.parametrize("db_error", [True, False])
def test_admin_admin_unit_update(client, seeder, utils, app, mocker, db, db_error):
    user_id, admin_unit_id = seeder.setup_base(True)

    with app.app_context():
        from project.models import AdminUnit

        admin_unit = AdminUnit.query.get_or_404(admin_unit_id)
        admin_unit.incoming_reference_requests_allowed = False
        admin_unit.suggestions_enabled = False
        admin_unit.can_create_other = False
        admin_unit.can_invite_other = False
        admin_unit.can_verify_other = False
        db.session.commit()

    url = utils.get_url("admin_admin_unit_update", id=admin_unit_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "incoming_reference_requests_allowed": "y",
            "suggestions_enabled": "y",
            "can_create_other": "y",
            "can_invite_other": "y",
            "can_verify_other": "y",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "admin_admin_units")

    with app.app_context():
        from project.models import AdminUnit

        admin_unit = AdminUnit.query.get_or_404(admin_unit_id)
        assert admin_unit.incoming_reference_requests_allowed
        assert admin_unit.suggestions_enabled
        assert admin_unit.can_create_other
        assert admin_unit.can_invite_other
        assert admin_unit.can_verify_other
