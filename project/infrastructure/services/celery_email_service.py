from project.application.read_models.mail_job_read_models import MailJob
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

        from project.infrastructure.celery_base_tasks import send_mail_with_body_task

        if len(signatures) == 0:  # pragma: no cover
            return

        result = group(
            send_mail_with_body_task.s(*signature) for signature in signatures
        ).delay()
        return result

    def send_mails_with_signatures_tracked(self, signatures) -> MailJob:
        from celery import group

        from project.infrastructure.celery_app import celery
        from project.infrastructure.celery_base_tasks import send_mail_with_body_task

        if len(signatures) == 0:
            return MailJob(count=0)

        result = group(
            send_mail_with_body_task.s(*signature) for signature in signatures
        ).delay()

        # Eager mode has no result backend: the tasks have already run.
        if celery.conf.task_always_eager:
            return MailJob(count=len(signatures))

        result.save()
        return MailJob(job_id=result.id, count=len(signatures))
