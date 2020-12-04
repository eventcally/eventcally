def test_send_mails(client, seeder, app, utils):
    from project.models import AdminUnitMemberInvitation
    from project.views.utils import send_mail

    user_id, admin_unit_id = seeder.setup_base()
    email = "new@member.de"
    invitation_id = seeder.create_invitation(admin_unit_id, email)

    with app.test_request_context():
        with app.app_context():
            from project import mail

            mail.default_sender = None
            invitation = AdminUnitMemberInvitation.query.get(invitation_id)
            send_mail(
                email,
                "You have received an invitation",
                "invitation_notice",
                invitation=invitation,
            )


def test_get_pagination_urls(client, seeder, app, utils):
    user_id, admin_unit_id = seeder.setup_base()

    for i in range(31):
        seeder.upsert_event_organizer(admin_unit_id, "Organizer %d" % i)

    utils.get_endpoint_ok(
        "manage_admin_unit_organizers", id=admin_unit_id, page=2, per_page=10
    )
