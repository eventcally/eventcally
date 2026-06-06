from project.application.services.abstract_email_service import AbstractEmailService


class CeleryEmailService(AbstractEmailService):
    def send_mails_with_signatures_async(self, signatures):
        from celery import group

        from project.base_tasks import send_mail_with_body_task

        if len(signatures) == 0:  # pragma: no cover
            return

        result = group(
            send_mail_with_body_task.s(*signature) for signature in signatures
        ).delay()
        return result
