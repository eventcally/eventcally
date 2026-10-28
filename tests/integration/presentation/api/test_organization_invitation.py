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
        from project.infrastructure.models import AdminUnitInvitation

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
        from project.infrastructure.models import AdminUnitInvitation

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
        from project.infrastructure.models import AdminUnitInvitation

        invitation = db.session.get(AdminUnitInvitation, invitation_id)
        assert invitation is None


def test_read_as_app_installation(client, seeder, utils):
    _, admin_unit_id = seeder.setup_api_access(as_app_installation=True)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    url = utils.get_url("api_v1_organization_invitation", id=invitation_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert response.json["id"] == invitation_id


def test_read_app_installation_without_permission(client, app, db, seeder, utils):
    _, admin_unit_id = seeder.setup_api_access(as_app_installation=True)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    with app.app_context():
        from project.infrastructure.models import AppInstallation

        for app_installation in AppInstallation.query.all():
            app_installation.permissions = ["organization_invitations:write"]

        db.session.commit()

    url = utils.get_url("api_v1_organization_invitation", id=invitation_id)
    response = utils.get_json(url)
    utils.assert_response_unauthorized(response)


# Organization-scoped routes


def _org_url(utils, admin_unit_id, invitation_id):
    return utils.get_url(
        "api_v1_organization_organization_invitation",
        id=admin_unit_id,
        organization_invitation_id=invitation_id,
    )


def test_organization_read(client, seeder, utils):
    _, admin_unit_id = seeder.setup_api_access()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    response = utils.get_json(_org_url(utils, admin_unit_id, invitation_id))
    utils.assert_response_ok(response)
    assert response.json["id"] == invitation_id
    assert response.json["organization"]["id"] == admin_unit_id


def test_organization_read_otherOrganization(client, seeder, utils):
    _, admin_unit_id = seeder.setup_api_access()
    other_user_id = seeder.create_user("other@test.de")
    other_admin_unit_id = seeder.create_admin_unit(other_user_id, "Other Crew")
    invitation_id = seeder.create_admin_unit_invitation(other_admin_unit_id)

    utils.assert_response_notFound(
        utils.get_json(_org_url(utils, admin_unit_id, invitation_id))
    )
    utils.assert_response_unauthorized(
        utils.get_json(_org_url(utils, other_admin_unit_id, invitation_id))
    )
    utils.assert_response_notFound(utils.get_json(_org_url(utils, admin_unit_id, 4711)))


def test_organization_put(client, app, seeder, utils, db):
    _, admin_unit_id = seeder.setup_api_access()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    response = utils.put_json(
        _org_url(utils, admin_unit_id, invitation_id),
        {
            "organization_name": "Invited Organization1",
            "relation_auto_verify_event_reference_requests": True,
            "relation_verify": True,
        },
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import AdminUnitInvitation

        invitation = db.session.get(AdminUnitInvitation, invitation_id)
        assert invitation.admin_unit_name == "Invited Organization1"
        assert invitation.relation_verify


def test_organization_patch(client, app, seeder, utils, db):
    _, admin_unit_id = seeder.setup_api_access()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    response = utils.patch_json(
        _org_url(utils, admin_unit_id, invitation_id),
        {"relation_auto_verify_event_reference_requests": True},
    )
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.infrastructure.models import AdminUnitInvitation

        invitation = db.session.get(AdminUnitInvitation, invitation_id)
        assert invitation.relation_auto_verify_event_reference_requests


def test_organization_delete(client, app, seeder, utils, db):
    _, admin_unit_id = seeder.setup_api_access()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    utils.assert_response_no_content(
        utils.delete(_org_url(utils, admin_unit_id, invitation_id))
    )

    with app.app_context():
        from project.infrastructure.models import AdminUnitInvitation

        assert db.session.get(AdminUnitInvitation, invitation_id) is None
