from project.application.services.abstract_email_service import AbstractEmailService
from project.application.services.abstract_localization_service import (
    AbstractLocalizationService,
)
from project.application.services.abstract_mail_sender import AbstractMailSender
from project.application.services.abstract_template_render_service import (
    AbstractTemplateRenderService,
)


class CeleryEmailService(AbstractEmailService):
    def __init__(
        self,
        default_locale,
        localization_service: AbstractLocalizationService,
        template_render_service: AbstractTemplateRenderService,
        mail_sender: AbstractMailSender,
    ):
        super().__init__(default_locale, localization_service, template_render_service)
        self.mail_sender = mail_sender

    def send_mails_with_signatures(self, signatures):
        for recipient, subject, body, html in signatures:
            self.mail_sender.send_mails_with_body([recipient], subject, body, html)

    def send_mails_with_signatures_async(self, signatures):
        from celery import group

        from project.base_tasks import send_mail_with_body_task

        if len(signatures) == 0:  # pragma: no cover
            return

        result = group(
            send_mail_with_body_task.s(*signature) for signature in signatures
        ).delay()
        return result
