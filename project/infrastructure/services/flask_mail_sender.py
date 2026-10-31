import logging

from flask_mail import Message

from project.application.services.abstract_mail_sender import AbstractMailSender
from project.infrastructure.extensions import mail

logger = logging.getLogger(__name__)


class FlaskMailSender(AbstractMailSender):
    def send_mails_with_body(self, recipients, subject, body, html):
        # Send single mails, otherwise recipients will see each other
        for recipient in recipients:
            msg = Message(subject)
            msg.recipients = [recipient]
            msg.body = body
            msg.html = html
            self._send_message(msg)

    def _send_message(self, msg):
        if not mail.default_sender:
            logger.info(
                "Mail not sent (no MAIL_DEFAULT_SENDER)",
                extra={
                    "recipients": msg.recipients,
                    "subject": msg.subject,
                    "body": msg.body,
                },
            )
            return

        mail.send(msg)  # pragma: no cover
