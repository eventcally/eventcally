"""Jinja/access helper query handlers — fake repositories, no database."""

from project.application import queries
from project.application.query_handlers import (
    GetCurrentMemberGrantsHandler,
    GetManageMenuOptionsHandler,
    GetSettingsHandler,
    GetSiteNoticesHandler,
    ListEventReportRecipientsHandler,
)
from project.application.read_models.access_helper_read_models import (
    ManageMenuOptionsReadModel,
    MemberGrantsReadModel,
)
from project.application.read_models.settings_read_model import SettingsReadModel
from project.application.read_models.site_notices_read_model import SiteNoticesReadModel
from project.application.read_repositories.abstract_site_settings_read_repository import (
    AbstractSiteSettingsReadRepository,
)
from project.domain.models.entities.actor import Actor
from tests.application.query_handlers.test_access_query_handlers import (
    FakeAccessRepo,
    _authz,
)


class FakeSettingsRepo(AbstractSiteSettingsReadRepository):
    def get_site_notices(self):
        return SiteNoticesReadModel(has_tos=True, announcement="Hi")

    def get_settings(self):
        return SettingsReadModel(tos="Terms", privacy="Privacy")


def _badges(handler, actor, admin_unit_id=1):
    return handler.handle(
        queries.GetManageMenuOptionsQuery(admin_unit_id=admin_unit_id, actor=actor)
    )


def test_manage_menu_options_without_user_are_zero():
    handler = GetManageMenuOptionsHandler(FakeAccessRepo(), _authz())

    assert _badges(handler, None) == ManageMenuOptionsReadModel()
    assert (
        _badges(handler, Actor(app_installation_id=3)) == ManageMenuOptionsReadModel()
    )


def test_manage_menu_options_for_member():
    handler = GetManageMenuOptionsHandler(FakeAccessRepo(), _authz())

    # user 7 is a member of organizations 3 and 1
    assert _badges(handler, Actor(user_id=7), 3).reference_requests_incoming_badge == 3


def test_manage_menu_options_for_platform_admin_who_is_not_a_member():
    handler = GetManageMenuOptionsHandler(FakeAccessRepo(), _authz(admins=[9]))

    assert _badges(handler, Actor(user_id=9), 2).reference_requests_incoming_badge == 2


def test_manage_menu_options_for_non_member_are_zero():
    handler = GetManageMenuOptionsHandler(FakeAccessRepo(), _authz())

    assert _badges(handler, Actor(user_id=7), 2) == ManageMenuOptionsReadModel()
    assert _badges(handler, Actor(user_id=8), 1) == ManageMenuOptionsReadModel()


def test_current_member_grants():
    handler = GetCurrentMemberGrantsHandler(FakeAccessRepo())

    def grants(actor):
        return handler.handle(
            queries.GetCurrentMemberGrantsQuery(admin_unit_id=1, actor=actor)
        )

    assert grants(None) == MemberGrantsReadModel()
    assert grants(Actor(app_installation_id=3)) == MemberGrantsReadModel()
    assert grants(Actor(user_id=7)) == MemberGrantsReadModel(
        roles=["admin"], permissions=["7:read"]
    )


def test_site_notices_pass_through():
    notices = GetSiteNoticesHandler(FakeSettingsRepo()).handle(
        queries.GetSiteNoticesQuery()
    )

    assert notices.has_tos is True
    assert notices.announcement == "Hi"


def test_settings_pass_through():
    settings = GetSettingsHandler(FakeSettingsRepo()).handle(queries.GetSettingsQuery())

    assert settings.tos == "Terms"
    assert settings.privacy == "Privacy"
    assert settings.contact is None


def test_event_report_recipients_ask_for_events_write():
    recipients = ListEventReportRecipientsHandler(FakeAccessRepo()).handle(
        queries.ListEventReportRecipientsQuery(admin_unit_id=4)
    )

    assert [(r.id, r.email) for r in recipients] == [(4, "events:write")]
