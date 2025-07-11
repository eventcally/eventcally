import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


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


def test_admin_units(client, seeder, utils: UtilActions, app):
    seeder.create_user(admin=True)
    user = utils.login()
    seeder.create_admin_unit(user, "Meine Crew")
    response = utils.get_endpoint("admin.organizations")
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

    utils.assert_response_redirect(response, "admin.admin")

    with app.app_context():
        from project.services.admin import upsert_settings

        settings = upsert_settings()
        assert settings.tos == "Meine Nutzungsbedingungen"
        assert settings.legal_notice == "Mein Impressum"
        assert settings.contact == "Mein Kontakt"
        assert settings.privacy == "Mein Datenschutz"


def test_admin_email(client, seeder, utils, app, mocker):
    user_id, admin_unit_id = seeder.setup_base(True)

    url = utils.get_url("admin_email")
    response = utils.get_ok(url)

    mail_mock = utils.mock_send_mails(mocker)
    response = utils.post_form(
        url,
        response,
        {
            "recipient": "test@test.de",
        },
    )

    utils.assert_response_ok(response)
    utils.assert_send_mail_called(mail_mock, "test@test.de")


def test_newsletter(app, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base(True)

    for i in range(10):
        locale = "de" if (i % 3) == 0 else "en" if (i % 3) == 1 else None
        seeder.create_user(f"test{i}@test.de", locale=locale)

    url = utils.get_url("admin_newsletter")
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "recipient_choice": 2,
            "message": "Message",
        },
    )

    utils.assert_response_ok(response)
    assert "result_id" in response.json


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
        set_roles_for_user(user.email, [])
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
@pytest.mark.parametrize("non_match", [True, False])
def test_user_delete(client, seeder, utils, app, db, mocker, db_error, non_match):
    user_id, admin_unit_id = seeder.setup_base(True)
    other_user_id = seeder.create_user("other@test.de")

    url = utils.get_url("admin_user_delete", id=other_user_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_email = "other@test.de"

    if non_match:
        form_email = "wrong@test.de"

    response = utils.post_form(
        url,
        response,
        {
            "email": form_email,
        },
    )

    if non_match:
        utils.assert_response_error_message(
            response, "Die eingegebene Email passt nicht zur Email des Nutzers"
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "admin_users")

    with app.app_context():
        from project.models import User

        user = db.session.get(User, other_user_id)
        assert user is None


@pytest.mark.parametrize("db_error", [True, False])
def test_admin_admin_unit_update(client, seeder, utils, app, mocker, db, db_error):
    user_id, admin_unit_id = seeder.setup_base(True)

    with app.app_context():
        from project.models import AdminUnit

        admin_unit = AdminUnit.query.get_or_404(admin_unit_id)
        admin_unit.incoming_reference_requests_allowed = False
        admin_unit.can_create_other = False
        admin_unit.can_invite_other = False
        admin_unit.can_verify_other = False
        db.session.commit()

    url = utils.get_url("admin.organization_update", id=admin_unit_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "incoming_reference_requests_allowed": "y",
            "can_create_other": "y",
            "can_invite_other": "y",
            "can_verify_other": "y",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "admin.organizations")

    with app.app_context():
        from project.models import AdminUnit

        admin_unit = AdminUnit.query.get_or_404(admin_unit_id)
        assert admin_unit.incoming_reference_requests_allowed
        assert admin_unit.can_create_other
        assert admin_unit.can_invite_other
        assert admin_unit.can_verify_other


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_admin_unit_delete(client, seeder, utils, app, db, mocker, db_error, non_match):
    user_id, admin_unit_id = seeder.setup_base(True)

    url = utils.get_url("admin.organization_delete", id=admin_unit_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    form_name = "Meine Crew"

    if non_match:
        form_name = "wrong"

    response = utils.post_form(
        url,
        response,
        {
            "name": form_name,
        },
    )

    if non_match:
        utils.assert_response_error_message(
            response, "Der eingegebene Name entspricht nicht dem Namen der Organisation"
        )
        return

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "admin.organizations")

    with app.app_context():
        from project.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        assert admin_unit is None


def test_admin_reset_tos_accepted(client, app, db, seeder: Seeder, utils: UtilActions):
    seeder.setup_base(admin=True)

    response = utils.get_endpoint_ok("admin_reset_tos_accepted")
    response = utils.post_form(
        response.request.url,
        response,
        {
            "reset_for_users": "y",
            "submit": "Reset",
        },
    )
    utils.assert_response_redirect(response, "admin.admin")

    with app.app_context():
        from project.models.user import User

        assert len(User.query.filter(User.tos_accepted_at.isnot(None)).all()) == 0


@pytest.mark.parametrize("db_error", [True, False])
def test_admin_planning(client, seeder, utils, app, mocker, db_error):
    user_id, admin_unit_id = seeder.setup_base(True)

    url = utils.get_url("admin_planning")
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(
        url,
        response,
        {
            "planning_external_calendars": "[]",
        },
    )

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "admin.admin")

    with app.app_context():
        from project.services.admin import upsert_settings

        settings = upsert_settings()
        assert settings.planning_external_calendars == "[]"
