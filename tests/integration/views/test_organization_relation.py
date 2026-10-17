from tests.integration.seeder import Seeder
from tests.integration.utils import UtilActions


def test_create(client, app, utils: UtilActions, seeder: Seeder, db):
    _, admin_unit_id = seeder.setup_base()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")

    with app.app_context():
        from project.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.can_verify_other = True
        db.session.commit()

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relation_create",
        id=admin_unit_id,
        target=other_admin_unit_id,
        verify=1,
    )
    response = utils.get_ok(url)

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relation_create",
        id=admin_unit_id,
    )
    lookup_response = utils.ajax_lookup(url, "target_admin_unit", "Other")
    assert lookup_response.json["items"][0][0] == other_admin_unit_id

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relation_create",
        id=admin_unit_id,
    )
    response = utils.post_form(
        url,
        response,
        {
            "target_admin_unit": other_admin_unit_id,
            "auto_verify_event_reference_requests": "y",
            "verify": "y",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.outgoing_organization_relations", id=admin_unit_id
    )

    with app.app_context():
        from project.models import AdminUnitRelation

        relation = (
            AdminUnitRelation.query.filter(
                AdminUnitRelation.source_admin_unit_id == admin_unit_id
            )
            .filter(AdminUnitRelation.target_admin_unit_id == other_admin_unit_id)
            .first()
        )
        assert relation is not None
        assert relation.auto_verify_event_reference_requests
        assert relation.verify


def test_update(client, app, utils, seeder, db):
    _, admin_unit_id = seeder.setup_base()
    (
        _,
        _,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    with app.app_context():
        from project.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.can_verify_other = True
        db.session.commit()

    url = utils.get_url(
        "manage_admin_unit.outgoing_organization_relation_update",
        id=admin_unit_id,
        organization_relation_id=relation_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "auto_verify_event_reference_requests": "y",
            "verify": "y",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.outgoing_organization_relations", id=admin_unit_id
    )

    with app.app_context():
        from project.models import AdminUnitRelation

        relation = db.session.get(AdminUnitRelation, relation_id)
        assert relation is not None
        assert relation.auto_verify_event_reference_requests
        assert relation.verify


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
        from project.models import AdminUnitRelation

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
