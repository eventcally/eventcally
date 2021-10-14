def test_organization_invitation_list(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    seeder.create_user("invited@test.de")
    utils.login("invited@test.de")

    url = utils.get_url("api_v1_user_organization_invitation_list")
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert len(response.json["items"]) == 1
    assert response.json["items"][0]["id"] == invitation_id
    assert response.json["items"][0]["email"] == "invited@test.de"
    assert response.json["items"][0]["organization_name"] == "Invited Organization"


def test_organization_invitation_read(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    seeder.create_user("invited@test.de")
    utils.login("invited@test.de")

    url = utils.get_url("api_v1_user_organization_invitation", id=invitation_id)
    response = utils.get_json(url)
    utils.assert_response_ok(response)
    assert response.json["id"] == invitation_id
    assert response.json["organization"]["id"] == admin_unit_id
    assert response.json["email"] == "invited@test.de"
    assert response.json["organization_name"] == "Invited Organization"
    assert response.json["relation_auto_verify_event_reference_requests"] is False
    assert response.json["relation_verify"] is False


def test_organization_invitation_read_wrongEmail(client, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    seeder.create_user("other@test.de")
    utils.login("other@test.de")

    url = utils.get_url("api_v1_user_organization_invitation", id=invitation_id)
    response = utils.get_json(url)
    utils.assert_response_unauthorized(response)


def test_organization_invitation_delete(client, app, seeder, utils):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    seeder.create_user("invited@test.de")
    utils.login("invited@test.de")

    url = utils.get_url(
        "api_v1_user_organization_invitation",
        id=invitation_id,
    )
    response = utils.delete(url)
    utils.assert_response_no_content(response)

    with app.app_context():
        from project.models import AdminUnitInvitation

        invitation = AdminUnitInvitation.query.get(invitation_id)
        assert invitation is None
