def test_create(client, app, utils, seeder):
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

    with app.app_context():
        app.test_event_dispatcher.handle_pending_events()

    invitation_url = utils.get_url(
        "main.user_organization_invitation",
        id=invitation.id,
    )

    assert len(app.test_email_service.sent_emails) == 1
    sent_email = app.test_email_service.sent_emails[0]
    assert sent_email["recipient"] == "invited@test.de"
    assert invitation_url in sent_email["body"]
    assert invitation_url in sent_email["html"]


def test_update(client, app, db, utils, seeder):
    _, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    with app.app_context():
        from project.models import AdminUnit

        admin_unit = db.session.get(AdminUnit, admin_unit_id)
        admin_unit.can_verify_other = True
        db.session.commit()

    url = utils.get_url(
        "manage_admin_unit.organization_invitation_update",
        id=admin_unit_id,
        organization_invitation_id=invitation_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "admin_unit_name": "Renamed Organization",
            "relation_auto_verify_event_reference_requests": True,
            "relation_verify": True,
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.organization_invitations", id=admin_unit_id
    )

    with app.app_context():
        from project.models import AdminUnitInvitation

        invitation = db.session.get(AdminUnitInvitation, invitation_id)
        assert invitation.admin_unit_name == "Renamed Organization"
        assert invitation.relation_auto_verify_event_reference_requests
        assert invitation.relation_verify


def test_revoke(client, app, db, utils, seeder):
    _, admin_unit_id = seeder.setup_base()
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)

    url = utils.get_url(
        "manage_admin_unit.organization_invitation_delete",
        id=admin_unit_id,
        organization_invitation_id=invitation_id,
    )
    response = utils.get_ok(url)

    response = utils.post_form(
        url,
        response,
        {
            "submit": "Submit",
        },
    )

    utils.assert_response_redirect(
        response, "manage_admin_unit.organization_invitations", id=admin_unit_id
    )

    with app.app_context():
        from project.models import AdminUnitInvitation

        assert db.session.get(AdminUnitInvitation, invitation_id) is None
