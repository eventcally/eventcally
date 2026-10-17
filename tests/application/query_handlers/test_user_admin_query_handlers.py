"""User admin query handlers — platform admins only."""

import pytest

from project.application import queries
from project.application.query_handlers import (
    GetUserForAdminHandler,
    ListNewsletterRecipientsHandler,
    ListRolesHandler,
    ListUsersForAdminHandler,
)
from project.application.read_models.page import Page
from project.application.read_models.user_admin_read_models import (
    NewsletterRecipientReadModel,
    RoleReadModel,
    UserAdminReadModel,
)
from project.application.read_repositories.abstract_user_admin_read_repository import (
    AbstractUserAdminReadRepository,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from tests.application.services.test_event_visibility_service import FakeReader


class FakeRepo(AbstractUserAdminReadRepository):
    def list_users(self, page_request):
        user = UserAdminReadModel(id=1, email="a@test.de")
        return Page[UserAdminReadModel](
            items=[user],
            page=page_request.page,
            per_page=page_request.per_page,
            total=1,
        )

    def get_user(self, user_id):
        return UserAdminReadModel(id=1, email="a@test.de") if user_id == 1 else None

    def list_roles(self):
        return [RoleReadModel(id=1, name="admin", title="Administrator")]

    def list_newsletter_recipients(self):
        return [NewsletterRecipientReadModel(id=1, email="a@test.de")]


def _handle(handler_class, query):
    return handler_class(
        FakeRepo(), ActorAuthorizationService(FakeReader(admins=[7]))
    ).handle(query)


ADMIN = Actor(user_id=7)


def test_platform_admins_read_users_roles_and_recipients():
    assert (
        _handle(
            ListUsersForAdminHandler, queries.ListUsersForAdminQuery(actor=ADMIN)
        ).total
        == 1
    )
    assert (
        _handle(
            GetUserForAdminHandler, queries.GetUserForAdminQuery(id=1, actor=ADMIN)
        ).email
        == "a@test.de"
    )
    assert (
        _handle(GetUserForAdminHandler, queries.GetUserForAdminQuery(id=2, actor=ADMIN))
        is None
    )
    assert [
        r.name for r in _handle(ListRolesHandler, queries.ListRolesQuery(actor=ADMIN))
    ] == ["admin"]
    assert (
        len(
            _handle(
                ListNewsletterRecipientsHandler,
                queries.ListNewsletterRecipientsQuery(actor=ADMIN),
            )
        )
        == 1
    )


@pytest.mark.parametrize("actor", [None, Actor(), Actor(user_id=9)])
@pytest.mark.parametrize(
    "handler_class, query_class",
    [
        (ListUsersForAdminHandler, queries.ListUsersForAdminQuery),
        (ListRolesHandler, queries.ListRolesQuery),
        (ListNewsletterRecipientsHandler, queries.ListNewsletterRecipientsQuery),
    ],
)
def test_everyone_else_is_refused(handler_class, query_class, actor):
    with pytest.raises(UnauthorizedError):
        _handle(handler_class, query_class(actor=actor))


def test_a_single_user_is_refused_too():
    with pytest.raises(UnauthorizedError):
        _handle(
            GetUserForAdminHandler,
            queries.GetUserForAdminQuery(id=1, actor=Actor(user_id=9)),
        )
