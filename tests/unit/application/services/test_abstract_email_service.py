"""Unit tests for AbstractEmailService behavior."""

from project.application.read_models.mail_job_read_models import MailJob
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

    def send_mails_with_signatures(self, signatures):
        self.sent_signatures = signatures

    def send_mails_with_signatures_async(self, signatures):
        self.sent_signatures = signatures
        return signatures

    def send_mails_with_signatures_tracked(self, signatures):
        self.sent_signatures = signatures
        return MailJob(job_id="job-1", count=len(signatures))


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

    def test_send_template_mail_to_address_sends_one_signature_sync(self):
        svc = _ConcreteEmailService()

        svc.send_template_mail_to_address(
            "a@example.com", "test_email", site_name="EventCally"
        )

        assert len(svc.sent_signatures) == 1
        email, subject, body, html = svc.sent_signatures[0]
        assert email == "a@example.com"
        assert subject.startswith("en:")
        assert body == "en:email/test_email.txt"
        assert html == "en:email/test_email.html"

    def test_base_send_mails_with_signatures_raises(self):
        svc = _ConcreteEmailService()

        try:
            AbstractEmailService.send_mails_with_signatures(svc, [])
            assert False, "Expected NotImplementedError"
        except NotImplementedError:
            pass

    def test_tracked_users_group_by_locale(self):
        svc = _ConcreteEmailService()
        users = [
            _User(email="b@example.com", locale="de"),
            _User(email="a@example.com", locale=""),
        ]

        job = svc.send_template_mails_to_users_tracked(
            users, "test_email", site_name="EventCally"
        )

        assert job == MailJob(job_id="job-1", count=2)
        assert [s[0] for s in svc.sent_signatures] == ["a@example.com", "b@example.com"]
        assert svc.sent_signatures[0][2].startswith("en:")
        assert svc.sent_signatures[1][2].startswith("de:")

    def test_tracked_users_empty_has_count_zero(self):
        svc = _ConcreteEmailService()

        job = svc.send_template_mails_to_users_tracked(
            [], "test_email", site_name="EventCally"
        )

        assert job == MailJob(job_id=None, count=0)
        assert svc.sent_signatures == []

    def test_tracked_address_has_count_one(self):
        svc = _ConcreteEmailService()

        job = svc.send_template_mail_to_address_tracked(
            "a@example.com", "test_email", site_name="EventCally"
        )

        assert job.count == 1
        assert svc.sent_signatures[0][0] == "a@example.com"

    def test_base_send_mails_with_signatures_tracked_raises(self):
        svc = _ConcreteEmailService()

        try:
            AbstractEmailService.send_mails_with_signatures_tracked(svc, [])
            assert False, "Expected NotImplementedError"
        except NotImplementedError:
            pass


class TestSendTemplateMailToAddressAsync:
    def test_sends_one_signature_async(self):
        svc = _ConcreteEmailService()

        result = svc.send_template_mail_to_address_async(
            "a@example.com", "test_email", site_name="EventCally"
        )

        assert result == svc.sent_signatures
        assert len(result) == 1
        email, subject, body, html = result[0]
        assert email == "a@example.com"
        assert body == "en:email/test_email.txt"
        assert html == "en:email/test_email.html"
