import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


def test_index_noCookie(client, seeder: Seeder, utils):
    user_id, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint("manage")
    utils.assert_response_redirect(response, "manage_admin_units")


def test_index_withValidCookie(client, seeder, app, utils):
    from flask_login.utils import encode_cookie

    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        encoded = encode_cookie(str(admin_unit_id))
        client.set_cookie("manage_admin_unit_id", encoded)

    response = utils.get_endpoint("manage")
    utils.assert_response_redirect(response, "manage_admin_unit", id=admin_unit_id)


def test_index_withInvalidCookie(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()
    client.set_cookie("manage_admin_unit_id", "invalid")

    response = utils.get_endpoint("manage")
    utils.assert_response_redirect(response, "manage_admin_units")


def test_index_after_login(client, app, db, utils, seeder):
    user_id, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint("manage_after_login")
    utils.assert_response_redirect(response, "manage", from_login=1)

    response = utils.get_endpoint("manage", from_login=1)
    utils.assert_response_redirect(response, "manage_admin_unit", id=admin_unit_id)


def test_index_after_login_with_invitation(client, app, db, utils, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "new@member.de"
    invitation_id = seeder.create_invitation(admin_unit_id, email)

    seeder.create_user(email)
    utils.login(email)

    response = utils.get_endpoint("manage_after_login")
    utils.assert_response_redirect(response, "manage", from_login=1)

    response = utils.get_endpoint("manage", from_login=1)
    utils.assert_response_redirect(
        response, "admin_unit_member_invitation", id=invitation_id
    )


def test_index_after_login_organization_invitation(client, app, db, utils, seeder):
    user_id = seeder.create_user()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    email = "invited@test.de"
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id, email)

    seeder.create_user(email)
    utils.login(email)

    response = utils.get_endpoint("manage_after_login")
    utils.assert_response_redirect(response, "manage", from_login=1)

    response = utils.get_endpoint("manage", from_login=1)
    utils.assert_response_redirect(
        response, "user_organization_invitation", id=invitation_id
    )


def test_admin_unit(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint("manage_admin_unit", id=admin_unit_id)
    utils.assert_response_redirect(
        response, "manage_admin_unit_events", id=admin_unit_id
    )


def test_admin_unit_404(client, seeder: Seeder, utils: UtilActions):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_user()
    utils.login()

    response = utils.get_endpoint("manage_admin_unit", id=admin_unit_id)
    utils.assert_response_notFound(response)


def test_admin_unit_events(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin_unit_verified=False)
    draft_id = seeder.create_event(admin_unit_id, draft=True)
    planned_id = seeder.create_event(admin_unit_id, planned=True)

    utils.get_endpoint_ok(
        "manage_admin_unit_events",
        id=admin_unit_id,
        date_from="2020-10-03",
        date_to="2021-10-03",
    )

    response = utils.get_endpoint_ok("manage_admin_unit_events", id=admin_unit_id)

    event_url = utils.get_url("event", event_id=draft_id)
    utils.assert_response_contains(response, event_url)

    planned_url = utils.get_url("event", event_id=planned_id)
    utils.assert_response_contains(response, planned_url)


def test_admin_unit_events_invalidDateFormat(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base()

    utils.get_endpoint_ok(
        "manage_admin_unit_events",
        id=admin_unit_id,
        date_from="03.10.2020",
        date_to="2021-10-03",
    )
    utils.get_endpoint_ok(
        "manage_admin_unit_events", id=admin_unit_id, date_from="", date_to=""
    )


def test_admin_unit_events_place(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base(admin_unit_verified=False)
    seeder.create_event(admin_unit_id, draft=True)
    event_place_id = seeder.upsert_default_event_place(admin_unit_id)

    utils.get_endpoint_ok(
        "manage_admin_unit_events", id=admin_unit_id, event_place_id=event_place_id
    )


def test_admin_unit_organizers(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()

    utils.get_endpoint_ok("manage_admin_unit.event_organizers", id=admin_unit_id)


def test_admin_unit_event_places(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()

    utils.get_endpoint_ok("manage_admin_unit.event_places", id=admin_unit_id)


def test_admin_unit_members(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()

    utils.get_endpoint_ok("manage_admin_unit.organization_members", id=admin_unit_id)


def test_admin_unit_members_permission_missing(
    client, seeder: Seeder, utils: UtilActions
):
    owner_id, admin_unit_id, member_id = seeder.setup_base_event_verifier()

    response = utils.get_endpoint(
        "manage_admin_unit.organization_members", id=admin_unit_id
    )
    utils.assert_response_permission_missing(
        response, "manage_admin_unit", id=admin_unit_id
    )


@pytest.mark.parametrize("db_error", [True, False])
def test_admin_unit_widgets(
    client, seeder: Seeder, utils: UtilActions, mocker, db_error
):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.widgets", id=admin_unit_id)
    response = utils.get_ok(url)

    if db_error:
        utils.mock_db_commit(mocker)

    response = utils.post_form(url, response, {})

    if db_error:
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(
        response, "manage_admin_unit.widgets", id=admin_unit_id
    )


def test_admin_unit_relations(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relations", id=admin_unit_id
    )
    utils.get_ok(url)


def test_admin_unit_organization_invitations(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit.organization_invitations", id=admin_unit_id)
    utils.get_ok(url)


def test_admin_unit_event_lists(client, seeder: Seeder, utils: UtilActions):
    user_id, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit_event_lists", id=admin_unit_id)
    utils.get_ok(url)


def test_admin_unit_custom_widgets(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url("manage_admin_unit_custom_widgets", id=admin_unit_id)
    utils.get_ok(url)


@pytest.mark.parametrize("scenario", ["db_error", "default", "last_admin", "non_match"])
def test_manage_admin_unit_delete_membership(
    client, utils: UtilActions, seeder: Seeder, app, db, mocker, scenario: str
):
    user_id, admin_unit_id = seeder.setup_base()

    with app.app_context():
        from project.services.admin_unit import get_member_for_admin_unit_by_user_id

        member = get_member_for_admin_unit_by_user_id(
            admin_unit_id,
            user_id,
        )
        member_id = member.id

    if not scenario == "last_admin":
        seeder.create_admin_unit_member(
            admin_unit_id, ["admin"], "admin.member@test.de"
        )

    url = utils.get_url(
        "user.organization_member_delete", organization_member_id=member_id
    )

    if scenario == "last_admin":
        response = utils.get(url, follow_redirects=True)
        utils.assert_response_error_message(
            response,
            "Der letzte verbleibende Administrator kann die Organisation nicht verlassen.",
        )
        return

    response = utils.get_ok(url)

    if scenario == "db_error":
        utils.mock_db_commit(mocker)

    form_name = "Meine Crew"

    if scenario == "non_match":
        form_name = "wrong"

    response = utils.post_form(
        url,
        response,
        {
            "name": form_name,
        },
    )

    if scenario == "non_match":
        utils.assert_response_error_message(
            response, "Der eingegebene Name entspricht nicht dem Namen der Organisation"
        )
        return

    if scenario == "db_error":
        utils.assert_response_db_error(response)
        return

    utils.assert_response_redirect(response, "user.organization_members")

    with app.app_context():
        from project.models import AdminUnitMember

        assert db.session.get(AdminUnitMember, member_id) is None
