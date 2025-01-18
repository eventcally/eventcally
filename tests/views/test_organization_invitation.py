def test_create(client, app, utils, seeder, mocker):
    mail_mock = utils.mock_send_mails_async(mocker)
    _, admin_unit_id = seeder.setup_base()

    url = utils.get_url(
        "manage_admin_unit.organization_invitation_create", id=admin_unit_id
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "email": "invited@test.de",
            "admin_unit_name": "Invited Organization",
            "relation_auto_verify_event_reference_requests": True,
            "relation_verify": True,
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.organization_invitations", id=admin_unit_id
    )

    with app.app_context():
        from project.models import AdminUnitInvitation

        invitation = (
            AdminUnitInvitation.query.filter(
                AdminUnitInvitation.admin_unit_id == admin_unit_id
            )
            .filter(AdminUnitInvitation.email == "invited@test.de")
            .first()
        )
        assert invitation is not None

    invitation_url = utils.get_url(
        "user_organization_invitation",
        id=invitation.id,
    )
    utils.assert_send_mail_called(mail_mock, "invited@test.de", invitation_url)
