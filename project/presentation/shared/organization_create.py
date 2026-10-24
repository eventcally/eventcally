from dataclasses import dataclass
from typing import Literal, Optional

from flask import current_app
from flask_security import current_user

from project.application.queries import GetUserOrganizationInvitationQuery
from project.application.read_models.organization_invitation_read_models import (
    OrganizationInvitationDetailReadModel,
)
from project.domain.errors import UnauthorizedError
from project.presentation.shared.access import can_create_admin_unit, has_access
from project.presentation.shared.current_admin_unit import get_current_admin_unit

OrganizationCreateDenial = Literal[
    "invitation_forbidden", "invitation_missing", "closed", "deletion_requested"
]


@dataclass
class OrganizationCreateGate:
    """Whether the current user may open the organization create form. The delivery
    channels map `denial` to their own response (redirect/flash or 403/404)."""

    invitation: Optional[OrganizationInvitationDetailReadModel] = None
    denial: Optional[OrganizationCreateDenial] = None


@dataclass
class EmbeddedRelationOptions:
    admin_unit: object
    can_verify: bool
    can_auto_verify: bool


def check_organization_create(invitation_id: Optional[int]) -> OrganizationCreateGate:
    if invitation_id is not None and invitation_id > 0:
        query_bus = current_app.container.cqrs.query_bus()

        try:
            invitation = query_bus.handle(
                GetUserOrganizationInvitationQuery(id=invitation_id)
            )
        except UnauthorizedError:
            return OrganizationCreateGate(denial="invitation_forbidden")

        if invitation is None:
            return OrganizationCreateGate(denial="invitation_missing")

        return OrganizationCreateGate(invitation=invitation)

    if not can_create_admin_unit():
        return OrganizationCreateGate(denial="closed")

    if current_user.deletion_requested_at:
        return OrganizationCreateGate(denial="deletion_requested")

    return OrganizationCreateGate()


def get_embedded_relation_options(
    invitation: Optional[OrganizationInvitationDetailReadModel],
) -> Optional[EmbeddedRelationOptions]:
    """The relation to the current organization that can be created along with the
    new one; `None` for invitations or without the needed permission."""
    if invitation:
        return None

    admin_unit = get_current_admin_unit()

    if not admin_unit or not has_access(
        admin_unit, "outgoing_organization_relations:write"
    ):
        return None

    can_verify = bool(admin_unit.can_verify_other)
    can_auto_verify = bool(admin_unit.incoming_reference_requests_allowed)

    if not (can_verify or can_auto_verify):
        return None

    return EmbeddedRelationOptions(admin_unit, can_verify, can_auto_verify)
