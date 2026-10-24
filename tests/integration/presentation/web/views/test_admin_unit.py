import pytest

from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_create_renders_vue_shell(client, utils: UtilActions, seeder: Seeder):
    seeder.create_user()
    utils.login()

    response = utils.get_ok(utils.get_url("manage.organization_create"))

    assert b'id="app"' in response.data
    assert b"manage" in response.data


def test_create_requires_login(client, utils: UtilActions):
    response = utils.get(utils.get_url("manage.organization_create"))

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_create_requiresAdmin_nonAdmin(client, app, utils: UtilActions, seeder: Seeder):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True

    seeder.create_user()
    utils.login()

    url = utils.get_url("manage.organization_create")
    response = utils.get(url)
    utils.assert_response_redirect(response, "main.manage_admin_units")
    with client.session_transaction() as session:
        assert any("geschlossenen Test-Phase" in str(m) for _, m in session["_flashes"])


def test_create_requiresAdmin_globalAdmin(
    client, app, utils: UtilActions, seeder: Seeder
):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    seeder.create_user(admin=True)
    utils.login()

    utils.get_ok(utils.get_url("manage.organization_create"))


def test_create_requiresAdmin_memberOfOrgWithoutFlag(
    client, app, utils: UtilActions, seeder: Seeder
):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    seeder.setup_base()

    url = utils.get_url("manage.organization_create")
    response = utils.get(url)
    utils.assert_response_redirect(response, "main.manage_admin_units")


def test_create_requiresAdmin_memberOfOrgWithFlag(
    client, app, utils: UtilActions, seeder: Seeder
):
    app.config["ADMIN_UNIT_CREATE_REQUIRES_ADMIN"] = True
    user_id = seeder.create_user(admin=False)
    utils.login()
    seeder.create_admin_unit(user_id, can_create_other=True)

    utils.get_ok(utils.get_url("manage.organization_create"))


def test_create_deletion_requested(client, app, db, utils: UtilActions, seeder: Seeder):
    import datetime

    user_id = seeder.create_user()
    utils.login()

    with app.app_context():
        from project.infrastructure.models import User

        db.session.get(User, user_id).deletion_requested_at = datetime.datetime.now(
            datetime.UTC
        )
        db.session.commit()

    response = utils.get(utils.get_url("manage.organization_create"))
    utils.assert_response_redirect(response, "main.profile")


def _invitation_id(seeder: Seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(
        user_id, can_invite_other=True, can_verify_other=True
    )
    return seeder.create_admin_unit_invitation(admin_unit_id)


def test_create_from_invitation(client, utils: UtilActions, seeder: Seeder):
    invitation_id = _invitation_id(seeder)
    seeder.create_user("invited@test.de")
    utils.login("invited@test.de")

    url = utils.get_url("manage.organization_create", invitation_id=invitation_id)
    response = utils.get_ok(url)

    assert b'id="app"' in response.data


def test_create_from_invitation_currentUserDoesNotMatchInvitationEmail(
    client, utils: UtilActions, seeder: Seeder
):
    invitation_id = _invitation_id(seeder)
    seeder.create_user("other@test.de")
    utils.login("other@test.de")

    url = utils.get_url("manage.organization_create", invitation_id=invitation_id)
    response = utils.get(url)
    utils.assert_response_redirect(response, "main.manage_admin_units")


def test_create_from_unknown_invitation(client, utils: UtilActions, seeder: Seeder):
    seeder.create_user()
    utils.login()

    url = utils.get_url("manage.organization_create", invitation_id=4711)
    assert utils.get(url).status_code == 404


def test_create_from_invalid_invitation_id_is_ignored(
    client, utils: UtilActions, seeder: Seeder
):
    seeder.create_user()
    utils.login()

    url = utils.get_url("manage.organization_create", invitation_id="abc")
    utils.get_ok(url)


def test_update_renders_vue_shell(client, utils: UtilActions, seeder: Seeder):
    user_id = seeder.create_user()
    utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    url = utils.get_url("manage_admin_unit.update", id=admin_unit_id)
    response = utils.get_ok(url)

    assert b'id="app"' in response.data
    assert b"manage" in response.data


def test_update_permission_missing(client, app, db, utils: UtilActions, seeder: Seeder):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member_event_verifier(admin_unit_id)
    utils.login()

    url = utils.get_url("manage_admin_unit.update", id=admin_unit_id)
    response = utils.get(url)
    assert response.status_code == 302


def test_list(client, app, utils: UtilActions, seeder: Seeder):
    seeder.create_user()
    user_id = utils.login()
    seeder.create_admin_unit(user_id, "Meine Crew")
    url = utils.get_url("main.manage_admin_units")
    response = utils.get_ok(url)
    assert b"Meine Crew" in response.data


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_admin_unit_request_deletion(
    client, seeder: Seeder, utils: UtilActions, app, db, mocker, db_error, non_match
):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.request_deletion", id=admin_unit_id)
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

    utils.assert_response_redirect(response, "main.manage_admin_unit", id=admin_unit_id)

    with app.app_context():
        from project.infrastructure.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        assert admin_unit.deletion_requested_at is not None

        app.test_event_dispatcher.handle_pending_events()

    assert (
        app.test_email_service.sent_emails[0]["subject"]
        == "Löschung der Organisation beantragt"
    )


@pytest.mark.parametrize("db_error", [True, False])
@pytest.mark.parametrize("non_match", [True, False])
def test_admin_unit_cancel_deletion(
    client, seeder: Seeder, utils: UtilActions, app, db, mocker, db_error, non_match
):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        import datetime

        from project.infrastructure.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.deletion_requested_at = datetime.datetime.now(datetime.UTC)
        db.session.commit()

    url = utils.get_url("manage_admin_unit.cancel_deletion", id=admin_unit_id)
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

    utils.assert_response_redirect(response, "main.manage_admin_unit", id=admin_unit_id)

    with app.app_context():
        from project.infrastructure.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        assert admin_unit.deletion_requested_at is None


def test_admin_unit_cancel_deletion_permission_missing(
    client, seeder: Seeder, utils: UtilActions, mocker
):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()

    response = utils.get_endpoint("manage_admin_unit.cancel_deletion", id=admin_unit_id)
    utils.assert_response_permission_missing(
        response, "main.manage_admin_unit", id=admin_unit_id
    )
