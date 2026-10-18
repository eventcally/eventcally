from project.application.services.abstract_mail_sender import AbstractMailSender
from project.infrastructure.services.celery_email_service import CeleryEmailService


class _RecordingMailSender(AbstractMailSender):
    def __init__(self):
        self.calls = []

    def send_mails_with_body(self, recipients, subject, body, html):
        self.calls.append((recipients, subject, body, html))


def test_send_mails_with_signatures_sends_single_mails(app):
    sender = _RecordingMailSender()
    service = CeleryEmailService(
        default_locale="de",
        localization_service=app.container.infrastructure.localization_service(),
        template_render_service=app.container.infrastructure.template_render_service(),
        mail_sender=sender,
    )

    service.send_mails_with_signatures(
        [("a@test.de", "S1", "B1", "<p>B1</p>"), ("b@test.de", "S2", "B2", "<p>B2</p>")]
    )

    assert sender.calls == [
        (["a@test.de"], "S1", "B1", "<p>B1</p>"),
        (["b@test.de"], "S2", "B2", "<p>B2</p>"),
    ]
