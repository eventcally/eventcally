def test_send_template_mails(client, seeder, app, db, utils):
    from project.presentation.shared.mail import send_template_mail

    user_id, admin_unit_id = seeder.setup_base()
    email = "new@member.de"
    invitation_id = seeder.create_invitation(admin_unit_id, email)

    with app.test_request_context():
        with app.app_context():
            from project import mail

            mail.default_sender = None
            send_template_mail(
                email,
                "invitation_notice",
                invitation_id=invitation_id,
                admin_unit_name="Meine Crew",
            )


def test_send_template_mail_async(client, seeder, app, db, utils):
    from project.presentation.shared.mail import send_template_mail_async

    _, admin_unit_id = seeder.setup_base()
    email = "new@member.de"
    invitation_id = seeder.create_invitation(admin_unit_id, email)

    with app.test_request_context():
        with app.app_context():
            from project import mail

            mail.default_sender = None
            send_template_mail_async(
                email,
                "invitation_notice",
                invitation_id=invitation_id,
                admin_unit_name="Meine Crew",
            )
