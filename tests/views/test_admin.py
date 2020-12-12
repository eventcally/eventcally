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
