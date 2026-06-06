"""Unit tests for AbstractEmailService behavior."""

from project.application.services.abstract_email_service import AbstractEmailService
from project.application.services.abstract_localization_service import (
    AbstractLocalizationService,
)
from project.application.services.abstract_template_render_service import (
    AbstractTemplateRenderService,
)


class _FakeLocalizationService(AbstractLocalizationService):
    def get_text(self, *args, **kwargs) -> str:
        return ""

    def get_text_with_locale(self, locale, key, **kwargs) -> str:
        return f"{locale}:{key}"


class _FakeTemplateRenderService(AbstractTemplateRenderService):
    def render_template(self, template_name_or_list: str | list[str], **context) -> str:
        return ""

    def render_template_with_locale(
        self, locale, template_name_or_list: str | list[str], **context
    ) -> str:
        return f"{locale}:{template_name_or_list}"


class _ConcreteEmailService(AbstractEmailService):
    def __init__(self):
        super().__init__(
            default_locale="en",
            localization_service=_FakeLocalizationService(),
            template_render_service=_FakeTemplateRenderService(),
        )
        self.sent_signatures = []

    def send_mails_with_signatures_async(self, signatures):
        self.sent_signatures = signatures
        return signatures


class _User:
    def __init__(self, email, locale):
        self.email = email
        self.locale = locale


class TestAbstractEmailService:
    def test_send_template_mails_groups_by_locale(self):
        svc = _ConcreteEmailService()
        users = [
            _User(email="b@example.com", locale="de"),
            _User(email="a@example.com", locale=""),
        ]

        signatures = svc.send_template_mails_to_users_async(
            users,
            "test_email",
            site_name="EventCally",
        )

        assert len(signatures) == 2
        assert signatures[0][0] == "a@example.com"
        assert signatures[1][0] == "b@example.com"

    def test_get_subject_for_unknown_template_raises(self):
        svc = _ConcreteEmailService()

        try:
            svc._get_subject_for_template("does_not_exist")
            assert False, "Expected ValueError"
        except ValueError:
            pass

    def test_render_mail_body_uses_default_locale(self):
        svc = _ConcreteEmailService()
        subject, body, html = svc._render_mail_body_with_subject(
            "test_email", site_name="EventCally"
        )

        assert subject.startswith("en:")
        assert body == "en:email/test_email.txt"
        assert html == "en:email/test_email.html"

    def test_base_send_mails_with_signatures_async_raises(self):
        svc = _ConcreteEmailService()

        try:
            AbstractEmailService.send_mails_with_signatures_async(svc, [])
            assert False, "Expected NotImplementedError"
        except NotImplementedError:
            pass
