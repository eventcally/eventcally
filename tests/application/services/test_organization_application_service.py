"""Unit tests for OrganizationApplicationService."""

from project.application.services.organization_application_service import (
    OrganizationApplicationService,
)

# ---------------------------------------------------------------------------
# Helpers — fake members and users
# ---------------------------------------------------------------------------


class _FakeMember:
    def __init__(self, user_id):
        self.user_id = user_id


class _FakeUser:
    def __init__(self, user_id):
        self.id = user_id


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestOrganizationApplicationService:
    def test_sends_emails_to_members_with_permission(self, uow, email_service):
        """Happy path: gets members → gets users → sends emails."""
        member1 = _FakeMember(user_id=10)
        member2 = _FakeMember(user_id=20)
        user1 = _FakeUser(user_id=10)
        user2 = _FakeUser(user_id=20)

        uow.organization_members.set_members_for(
            admin_unit_id=1,
            permission="settings:write",
            members=[member1, member2],
        )
        uow.users._store[10] = user1
        uow.users._store[20] = user2

        service = OrganizationApplicationService(email_service=email_service)
        service.send_template_mails_to_members_async(
            uow,
            admin_unit_id=1,
            permission="settings:write",
            template="my_template",
            some_key="some_val",
        )

        assert len(email_service.calls) == 1
        call = email_service.calls[0]
        assert call["users"] == [user1, user2]
        assert call["template"] == "my_template"
        assert call["context"] == {"some_key": "some_val"}

    def test_no_members_does_not_send_email(self, uow, email_service):
        service = OrganizationApplicationService(email_service=email_service)
        service.send_template_mails_to_members_async(
            uow,
            admin_unit_id=1,
            permission="settings:write",
            template="t",
        )

        assert len(email_service.calls) == 1
        call = email_service.calls[0]
        assert call["users"] == []
        assert call["template"] == "t"

    def test_context_kwargs_forwarded_to_email_service(self, uow, email_service):
        service = OrganizationApplicationService(email_service=email_service)
        service.send_template_mails_to_members_async(
            uow,
            admin_unit_id=1,
            permission="p",
            template="tmpl",
            admin_unit="org_obj",
            extra=42,
        )

        assert len(email_service.calls) == 1
        call = email_service.calls[0]
        assert call["users"] == []
        assert call["template"] == "tmpl"
        assert call["context"] == {"admin_unit": "org_obj", "extra": 42}
