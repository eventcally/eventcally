def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_relation",
        id=relation_id,
    )
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert response.json["id"] == relation_id
    assert response.json["source_organization"]["id"] == admin_unit_id
    assert response.json["target_organization"]["id"] == other_admin_unit_id
    assert response.json["auto_verify_event_reference_requests"] is False


def test_read_unauthorized(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access(admin=False)
    second_user_id = seeder.create_user("second@test.de")
    second_admin_unit_id = seeder.create_admin_unit(second_user_id, "Second Crew")
    (
        third_user_id,
        third_admin_unit_id,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(second_admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_relation",
        id=relation_id,
    )
    response = utils.get_json(url)
    utils.assert_response_unauthorized(response)


def test_put(client, app, seeder, utils, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    with app.app_context():
        from project.infrastructure.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.can_verify_other = True
        db.session.commit()

    data = {
        "auto_verify_event_reference_requests": True,
        "verify": True,
    }

    url = utils.get_url(
        "api_v1_organization_relation",
        id=relation_id,
    )
    response = utils.put_json(url, data)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import AdminUnitRelation

        relation = db.session.get(AdminUnitRelation, relation_id)
        assert relation is not None
        assert relation.source_admin_unit_id == admin_unit_id
        assert relation.target_admin_unit_id == other_admin_unit_id
        assert relation.auto_verify_event_reference_requests
        assert relation.verify


def test_patch(client, app, seeder, utils, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    data = {
        "auto_verify_event_reference_requests": True,
    }

    url = utils.get_url(
        "api_v1_organization_relation",
        id=relation_id,
    )
    response = utils.patch_json(url, data)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import AdminUnitRelation

        relation = db.session.get(AdminUnitRelation, relation_id)
        assert relation is not None
        assert relation.source_admin_unit_id == admin_unit_id
        assert relation.target_admin_unit_id == other_admin_unit_id
        assert relation.auto_verify_event_reference_requests


def test_delete(client, app, seeder, utils, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    (
        other_user_id,
        other_admin_unit_id,
        relation_id,
    ) = seeder.create_any_admin_unit_relation(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_relation",
        id=relation_id,
    )
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import AdminUnitRelation

        relation = db.session.get(AdminUnitRelation, relation_id)
        assert relation is None


# Organization-scoped routes


def _url(utils, admin_unit_id, relation_id):
    return utils.get_url(
        "api_v1_organization_outgoing_organization_relation",
        id=admin_unit_id,
        organization_relation_id=relation_id,
    )


def test_organization_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, other_admin_unit_id, relation_id = seeder.create_any_admin_unit_relation(
        admin_unit_id
    )

    response = utils.get_json(_url(utils, admin_unit_id, relation_id))
    utils.assert_response_ok(response)
    assert response.json["id"] == relation_id
    assert response.json["source_organization"]["id"] == admin_unit_id
    assert response.json["target_organization"]["id"] == other_admin_unit_id


def test_organization_read_asTarget(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    relation_id = seeder.create_admin_unit_relation(other_admin_unit_id, admin_unit_id)

    utils.assert_response_notFound(
        utils.get_json(_url(utils, admin_unit_id, relation_id))
    )


def test_organization_read_unauthorized(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access(admin=False)
    second_user_id = seeder.create_user("second@test.de")
    second_admin_unit_id = seeder.create_admin_unit(second_user_id, "Second Crew")
    _, _, relation_id = seeder.create_any_admin_unit_relation(second_admin_unit_id)

    utils.assert_response_unauthorized(
        utils.get_json(_url(utils, second_admin_unit_id, relation_id))
    )
    utils.assert_response_notFound(
        utils.get_json(_url(utils, admin_unit_id, relation_id))
    )


def test_organization_put(client, app, seeder, utils, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, relation_id = seeder.create_any_admin_unit_relation(admin_unit_id)

    with app.app_context():
        from project.infrastructure.models import AdminUnit

        db.session.get(AdminUnit, admin_unit_id).can_verify_other = True
        db.session.commit()

    response = utils.put_json(
        _url(utils, admin_unit_id, relation_id),
        {"auto_verify_event_reference_requests": True, "verify": True},
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import AdminUnitRelation

        relation = db.session.get(AdminUnitRelation, relation_id)
        assert relation.auto_verify_event_reference_requests
        assert relation.verify


def test_organization_patch(client, app, seeder, utils, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, relation_id = seeder.create_any_admin_unit_relation(admin_unit_id)

    response = utils.patch_json(
        _url(utils, admin_unit_id, relation_id),
        {"auto_verify_event_reference_requests": True},
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import AdminUnitRelation

        relation = db.session.get(AdminUnitRelation, relation_id)
        assert relation.auto_verify_event_reference_requests


def test_organization_delete(client, app, seeder, utils, db):
    user_id, admin_unit_id = seeder.setup_api_access()
    _, _, relation_id = seeder.create_any_admin_unit_relation(admin_unit_id)

    utils.assert_response_no_content(
        utils.delete(_url(utils, admin_unit_id, relation_id))
    )

    with app.app_context():
        from project.infrastructure.models import AdminUnitRelation

        assert db.session.get(AdminUnitRelation, relation_id) is None


def test_organization_write_asTarget(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    relation_id = seeder.create_admin_unit_relation(other_admin_unit_id, admin_unit_id)
    url = _url(utils, admin_unit_id, relation_id)

    utils.assert_response_notFound(utils.patch_json(url, {"verify": False}))
    utils.assert_response_notFound(utils.delete(url))
