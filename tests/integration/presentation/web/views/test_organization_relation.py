from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_create(client, app, utils: UtilActions, seeder: Seeder, db):
    _, admin_unit_id = seeder.setup_base()
    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relation_create", id=admin_unit_id
    )

    # The page is a Vue 3 shell, the form reads and saves through the BFF.
    response = utils.get_ok(url)
    assert b'id="app"' in response.data


def test_create_requires_permission(client, seeder, utils: UtilActions):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    response = utils.get_endpoint(
        "manage_admin_unit.outgoing_organization_relation_create", id=admin_unit_id
    )
    utils.assert_response_permission_missing(
        response, "main.manage_admin_unit", id=admin_unit_id
    )


def test_update(client, app, utils, seeder, db):
    _, admin_unit_id = seeder.setup_base()
    (
        _,
        _,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relation_update",
        id=admin_unit_id,
        organization_relation_id=relation_id,
    )
    response = utils.get_ok(url)
    assert b'id="app"' in response.data


def test_update_of_another_organization_is_unauthorized(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base()
    other_admin_unit_id = seeder.create_admin_unit(
        seeder.create_user("third@test.de"), "Third Crew"
    )
    relation_id = seeder.create_admin_unit_relation(other_admin_unit_id, admin_unit_id)

    response = utils.get(
        utils.get_url(
            "manage_admin_unit.outgoing_organization_relation_update",
            id=admin_unit_id,
            organization_relation_id=relation_id,
        )
    )
    utils.assert_response_unauthorized(response)


def test_delete_page_is_removed(client, utils, seeder):
    _, admin_unit_id = seeder.setup_base()
    _, _, relation_id = seeder.create_any_admin_unit_relation(admin_unit_id)

    # Deleting is a modal of the list (`/bff/manage`).
    response = utils.get(
        f"/manage/admin_unit/{admin_unit_id}/outgoing_organization_relation/{relation_id}/delete"
    )

    utils.assert_response_notFound(response)


def test_list(client, utils: UtilActions, seeder: Seeder):
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relations", id=admin_unit_id
    )
    response = utils.get_ok(url)
    assert b'id="app"' in response.data

    # The filters are read by the Vue page from the query string.
    utils.get_ok(url + "?keyword=alp&verify=1&auto_verify_event_reference_requests=0")


def test_list_requires_permission(client, seeder, utils: UtilActions):
    owner_id = seeder.create_user("owner@owner")
    admin_unit_id = seeder.create_admin_unit(owner_id, "Other crew")
    seeder.create_admin_unit_member(admin_unit_id, [])
    utils.login()

    response = utils.get_endpoint(
        "manage_admin_unit.outgoing_organization_relations", id=admin_unit_id
    )
    utils.assert_response_permission_missing(
        response, "main.manage_admin_unit", id=admin_unit_id
    )
