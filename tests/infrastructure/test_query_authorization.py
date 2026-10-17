"""S2 done criterion: query handlers authorize the actor themselves.

Goes through the real query bus, so the handler's own check is exercised — the HTTP
decorators would otherwise mask it.
"""

import pytest

from project.application.queries import (
    GetOrganizationInvitationQuery,
    ListOrganizationInvitationsQuery,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor


@pytest.fixture
def scenario(app, db, seeder):
    _, admin_unit_id = seeder.setup_base(log_in=False)
    invitation_id = seeder.create_admin_unit_invitation(admin_unit_id)
    allowed_client_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=admin_unit_id
    )
    denied_client_id = seeder.insert_default_oauth2_client_app(
        admin_unit_id=admin_unit_id,
        app_permissions=["organization_invitations:write"],
    )

    return {
        "admin_unit_id": admin_unit_id,
        "invitation_id": invitation_id,
        "allowed": Actor(
            app_installation_id=seeder.install_app(allowed_client_id, admin_unit_id)
        ),
        "denied": Actor(
            app_installation_id=seeder.install_app(denied_client_id, admin_unit_id)
        ),
    }


def _handle(app, query):
    with app.app_context():
        return app.container.cqrs.query_bus().handle(query)


def test_list_refuses_an_installation_without_the_permission(app, scenario):
    query = ListOrganizationInvitationsQuery(
        admin_unit_id=scenario["admin_unit_id"], actor=scenario["denied"]
    )

    with pytest.raises(UnauthorizedError):
        _handle(app, query)


def test_list_serves_an_installation_with_the_permission(app, scenario):
    query = ListOrganizationInvitationsQuery(
        admin_unit_id=scenario["admin_unit_id"], actor=scenario["allowed"]
    )

    page = _handle(app, query)

    assert [item.id for item in page.items] == [scenario["invitation_id"]]


def test_get_refuses_an_installation_without_the_permission(app, scenario):
    query = GetOrganizationInvitationQuery(
        id=scenario["invitation_id"], actor=scenario["denied"]
    )

    with pytest.raises(UnauthorizedError):
        _handle(app, query)


def test_get_serves_an_installation_with_the_permission(app, scenario):
    query = GetOrganizationInvitationQuery(
        id=scenario["invitation_id"], actor=scenario["allowed"]
    )

    detail = _handle(app, query)

    assert detail.id == scenario["invitation_id"]
