import pytest

from tests.seeder import Seeder
from tests.utils import UtilActions


def test_update(client, app, utils: UtilActions, seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    member_id = seeder.create_admin_unit_member_event_verifier(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.organization_member_update",
        id=admin_unit_id,
        organization_member_id=member_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "role_names": "admin",
            "submit": "Submit",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.organization_members", id=admin_unit_id
    )

    with app.app_context():
        from project.services.admin_unit import get_admin_unit_member

        member = get_admin_unit_member(member_id)
        assert len(member.roles) == 1
        assert any(r.name == "admin" for r in member.roles)


def test_update_self(client, app, utils: UtilActions, seeder: Seeder):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")

    with app.app_context():
        from project.services.admin_unit import get_member_for_admin_unit_by_user_id

        member = get_member_for_admin_unit_by_user_id(admin_unit_id, user_id)
        member_id = member.id

    url = utils.get_url(
        "manage_admin_unit.organization_member_update",
        id=admin_unit_id,
        organization_member_id=member_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "role_names": "event_verifier",
            "submit": "Submit",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.organization_members", id=admin_unit_id
    )

    with app.app_context():
        from project.services.admin_unit import get_admin_unit_member

        member = get_admin_unit_member(member_id)
        assert len(member.roles) == 2
        assert any(r.name == "event_verifier" for r in member.roles)
        assert any(r.name == "admin" for r in member.roles)


@pytest.mark.parametrize("scenario", ["default", "current_user"])
def test_delete(client, app, db, utils: UtilActions, seeder: Seeder, scenario: str):
    seeder.create_user()
    user_id = utils.login()
    admin_unit_id = seeder.create_admin_unit(user_id, "Meine Crew")
    member_email = "test@test.de" if scenario == "current_user" else "member@test.de"
    member_id = seeder.create_admin_unit_member_event_verifier(
        admin_unit_id, email=member_email
    )

    url = utils.get_url(
        "manage_admin_unit.organization_member_delete",
        id=admin_unit_id,
        organization_member_id=member_id,
    )
    response = utils.get(url)

    if scenario == "current_user":
        utils.assert_response_redirect(
            response,
            "user.organization_member_delete",
            organization_member_id=member_id,
        )
        return

    utils.assert_response_ok(response)

    response = utils.post_form(
        url,
        response,
        {
            "submit": "Submit",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.organization_members", id=admin_unit_id
    )

    with app.app_context():
        from project.services.admin_unit import get_admin_unit_member

        member = get_admin_unit_member(member_id)
        assert member is None
