import abc
from itertools import groupby

from project.application.services.abstract_localization_service import (
    AbstractLocalizationService,
)
from project.application.services.abstract_template_render_service import (
    AbstractTemplateRenderService,
)


class AbstractEmailService(abc.ABC):
    def __init__(
        self,
        default_locale,
        localization_service: AbstractLocalizationService,
        template_render_service: AbstractTemplateRenderService,
    ):
        self.default_locale = default_locale
        self.localization_service = localization_service
        self.template_render_service = template_render_service
        self.mail_template_subject_mapping = None

    def send_template_mails_to_users_async(self, users, template, **context):
        if len(users) == 0:  # pragma: no cover
            return

        # Group by locale
        def locale_func(user):
            return user.locale if user.locale else ""

        sorted_users = sorted(users, key=locale_func)
        grouped_users = groupby(sorted_users, locale_func)

        signatures = list()

        for locale, locale_users in grouped_users:
            context["locale"] = locale
            subject, body, html = self._render_mail_body_with_subject(
                template, **context
            )
            signatures.extend(
                [(user.email, subject, body, html) for user in locale_users]
            )

        return self.send_mails_with_signatures_async(signatures)

    def _get_subject_for_template(self, template):
        if self.mail_template_subject_mapping is None:

            def dummy_gettext(message: str):
                return message

            self.mail_template_subject_mapping = {
                "event_report_notice": dummy_gettext("New event report"),
                "invitation_notice": dummy_gettext("You have received an invitation"),
                "newsletter": dummy_gettext("Newsletter from %(site_name)s"),
                "organization_deletion_requested_notice": dummy_gettext(
                    "Organization deletion requested"
                ),
                "organization_invitation_accepted_notice": dummy_gettext(
                    "Organization invitation accepted"
                ),
                "organization_invitation_notice": dummy_gettext(
                    "You have received an invitation"
                ),
                "reference_auto_verified_notice": dummy_gettext(
                    "New reference automatically verified"
                ),
                "reference_request_notice": dummy_gettext("New reference request"),
                "reference_request_review_status_notice": dummy_gettext(
                    "Event review status updated"
                ),
                "referenced_event_changed_notice": dummy_gettext(
                    "Referenced event changed"
                ),
                "review_notice": dummy_gettext("New event review"),
                "review_status_notice": dummy_gettext("Event review status updated"),
                "user_deletion_requested_notice": dummy_gettext(
                    "User deletion requested"
                ),
                "test_email": dummy_gettext("Test mail from %(site_name)s"),
                "verification_request_notice": dummy_gettext(
                    "New verification request"
                ),
                "verification_request_review_status_notice": dummy_gettext(
                    "Verification request review status updated"
                ),
            }
        subject_key = self.mail_template_subject_mapping.get(template, None)
        if subject_key is None:
            raise ValueError("No subject found for template %s" % template)
        return subject_key

    def _render_mail_body_with_subject(self, template, **context):
        subject_key = self._get_subject_for_template(template)
        locale = context.pop("locale", None) or self.default_locale

        subject = self.localization_service.get_text_with_locale(
            locale, subject_key, **context
        )
        body = self.template_render_service.render_template_with_locale(
            locale, "email/%s.txt" % template, **context
        )
        html = self.template_render_service.render_template_with_locale(
            locale, "email/%s.html" % template, **context
        )

        return subject, body, html

    @abc.abstractmethod
    def send_mails_with_signatures_async(self, signatures):  # pragma: no cover
        raise NotImplementedError
