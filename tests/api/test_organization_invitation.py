def test_read(client, seeder, utils):
    user_id, admin_unit_id = seeder.setup_api_access()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_invitation",
        id=invitation_id,
    )
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert response.json["id"] == invitation_id
    assert response.json["organization"]["id"] == admin_unit_id
    assert response.json["email"] == "invited@test.de"
    assert response.json["organization_name"] == "Invited Organization"
    assert response.json["relation_auto_verify_event_reference_requests"] is False
    assert response.json["relation_verify"] is False


def test_put(client, app, seeder, utils, db):
    _, admin_unit_id = seeder.setup_api_access()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    data = {
        "organization_name": "Invited Organization1",
        "relation_auto_verify_event_reference_requests": True,
        "relation_verify": True,
    }

    url = utils.get_url(
        "api_v1_organization_invitation",
        id=invitation_id,
    )
    response = utils.put_json(url, data)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import AdminUnitInvitation

        invitation = db.session.get(AdminUnitInvitation, invitation_id)
        assert invitation is not None
        assert invitation.admin_unit_id == admin_unit_id
        assert invitation.email == "invited@test.de"
        assert invitation.admin_unit_name == "Invited Organization1"
        assert invitation.relation_auto_verify_event_reference_requests
        assert invitation.relation_verify


def test_patch(client, app, seeder, utils, db):
    _, admin_unit_id = seeder.setup_api_access()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    data = {
        "relation_auto_verify_event_reference_requests": True,
    }

    url = utils.get_url(
        "api_v1_organization_invitation",
        id=invitation_id,
    )
    response = utils.patch_json(url, data)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import AdminUnitInvitation

        invitation = db.session.get(AdminUnitInvitation, invitation_id)
        assert invitation is not None
        assert invitation.admin_unit_id == admin_unit_id
        assert invitation.relation_auto_verify_event_reference_requests


def test_delete(client, app, seeder, utils, db):
    _, admin_unit_id = seeder.setup_api_access()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    url = utils.get_url(
        "api_v1_organization_invitation",
        id=invitation_id,
    )
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import AdminUnitInvitation

        invitation = db.session.get(AdminUnitInvitation, invitation_id)
        assert invitation is None
