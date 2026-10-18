from project.infrastructure.services.flask_mail_sender import FlaskMailSender


def test_send_mails_with_body_logs_without_default_sender(app):
    from project.extensions import mail

    with app.test_request_context():
        mail.default_sender = None
        FlaskMailSender().send_mails_with_body(
            ["a@test.de", "b@test.de"], "Subject", "Body", "<p>Body</p>"
        )
