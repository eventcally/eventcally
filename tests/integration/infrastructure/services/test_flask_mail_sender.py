import logging

from project.infrastructure.services.flask_mail_sender import FlaskMailSender


def test_send_mails_with_body_logs_without_default_sender(app, caplog):
    from project.infrastructure.extensions import mail

    with app.test_request_context():
        mail.default_sender = None
        with caplog.at_level(
            logging.INFO, logger="project.infrastructure.services.flask_mail_sender"
        ):
            FlaskMailSender().send_mails_with_body(
                ["a@test.de", "b@test.de"], "Subject", "Body", "<p>Body</p>"
            )

    records = [r for r in caplog.records if r.getMessage().startswith("Mail not sent")]
    assert [r.recipients for r in records] == [["a@test.de"], ["b@test.de"]]
    assert records[0].subject == "Subject"
    assert records[0].body == "Body"
