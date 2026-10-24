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


def test_delete(client, app, utils, seeder, db):
    _, admin_unit_id = seeder.setup_base()
    (
        _,
        _,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relation_delete",
        id=admin_unit_id,
        organization_relation_id=relation_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {},
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.outgoing_organization_relations", id=admin_unit_id
    )

    with app.app_context():
        from project.infrastructure.models import AdminUnitRelation

        relation = db.session.get(AdminUnitRelation, relation_id)
        assert relation is None


def test_list_keyword_and_filters(client, app, utils: UtilActions, seeder: Seeder):
    user_id, admin_unit_id = seeder.setup_base()
    alpha_id = seeder.create_admin_unit(
        seeder.create_user("alpha@test.de"), "Alpha Crew"
    )
    beta_id = seeder.create_admin_unit(seeder.create_user("beta@test.de"), "Beta Crew")
    seeder.create_admin_unit_relation(admin_unit_id, alpha_id, verify=True)
    seeder.create_admin_unit_relation(
        admin_unit_id, beta_id, auto_verify_event_reference_requests=True
    )

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relations", id=admin_unit_id
    )
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "Alpha Crew")
    utils.assert_response_contains(response, "Beta Crew")

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relations",
        id=admin_unit_id,
        keyword="alp",
    )
    response = utils.get_ok(url)
    utils.assert_response_contains(response, "Alpha Crew")
    utils.assert_response_contains_not(response, "Beta Crew")

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relations",
        id=admin_unit_id,
        auto_verify_event_reference_requests="1",
    )
    response = utils.get_ok(url)
    utils.assert_response_contains_not(response, "Alpha Crew")
    utils.assert_response_contains(response, "Beta Crew")
