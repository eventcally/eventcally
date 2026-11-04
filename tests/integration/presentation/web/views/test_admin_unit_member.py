from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_list_is_a_shell(client, seeder: Seeder, utils: UtilActions):
    _, admin_unit_id = seeder.setup_base()

    response = utils.get_endpoint_ok(
        "manage_admin_unit.organization_members", id=admin_unit_id
    )

    utils.assert_response_contains(response, 'id="boot"')


def test_list_of_a_foreign_organization_is_not_found(
    client, seeder: Seeder, utils: UtilActions
):
    user_id, admin_unit_id = seeder.setup_base()
    other_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Andere Crew"
    )

    utils.assert_response_notFound(
        utils.get(utils.get_url("manage_admin_unit.organization_members", id=other_id))
    )


def test_update_and_delete_pages_are_gone(client, seeder: Seeder, utils: UtilActions):
    """Changing the roles and removing a member are modals of the list."""
    _, admin_unit_id = seeder.setup_base()
    member_id = seeder.create_admin_unit_member_event_verifier(
        admin_unit_id, email="member@test.de"
    )

    for action in ("update", "delete"):
        utils.assert_response_notFound(
            utils.get(
                f"/manage/admin_unit/{admin_unit_id}/organization_member/{member_id}/{action}"
            )
        )
