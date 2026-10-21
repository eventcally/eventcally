import pytest

from project.application import commands
from project.application.command_handlers.send_test_mail_handler import (
    SendTestMailHandler,
)
from project.domain.errors import BaseError, MailDeliveryError, UnauthorizedError
from project.domain.models.aggregates.user_aggregate import UserAggregate
from tests.unit.application.conftest import ACTOR, ACTOR_USER_ID, FakeEmailService


def _make_admin(uow):
    uow.users.add(
        UserAggregate(
            id=ACTOR_USER_ID, email="admin@test.de", locale=None, is_platform_admin=True
        )
    )


def _cmd(asynchronous=False):
    return commands.SendTestMailCommand.model_construct(
        actor=ACTOR, recipient="to@test.de", asynchronous=asynchronous
    )


class TestSendTestMailHandler:
    def test_sync_sends_one_mail(self, uow):
        _make_admin(uow)
        email_service = FakeEmailService()

        result = SendTestMailHandler(email_service, "Site").handle(_cmd(), uow)

        assert result.job_id is None
        assert result.count == 1
        assert email_service.calls[0]["email"] == "to@test.de"
        assert email_service.calls[0]["template"] == "test_email"
        assert email_service.calls[0]["context"] == {"site_name": "Site"}

    def test_sync_failure_keeps_original_text(self, uow):
        _make_admin(uow)
        email_service = FakeEmailService(raise_on_send=Exception("SMTP down"))

        with pytest.raises(MailDeliveryError) as exc:
            SendTestMailHandler(email_service, "Site").handle(_cmd(), uow)

        assert exc.value.message == "SMTP down"

    def test_sync_failure_without_text_uses_default(self, uow):
        _make_admin(uow)
        email_service = FakeEmailService(raise_on_send=Exception())

        with pytest.raises(MailDeliveryError) as exc:
            SendTestMailHandler(email_service, "Site").handle(_cmd(), uow)

        assert exc.value.message == MailDeliveryError.default_message

    def test_sync_domain_error_is_not_wrapped(self, uow):
        _make_admin(uow)
        error = BaseError("domain")
        email_service = FakeEmailService(raise_on_send=error)

        with pytest.raises(BaseError) as exc:
            SendTestMailHandler(email_service, "Site").handle(_cmd(), uow)

        assert exc.value is error

    def test_async_returns_job(self, uow):
        _make_admin(uow)
        email_service = FakeEmailService()

        result = SendTestMailHandler(email_service, "Site").handle(
            _cmd(asynchronous=True), uow
        )

        assert result.job_id == "job-1"
        assert result.count == 1

    def test_non_admin_is_unauthorized(self, uow):
        email_service = FakeEmailService()

        with pytest.raises(UnauthorizedError):
            SendTestMailHandler(email_service, "Site").handle(_cmd(), uow)

        assert email_service.calls == []
