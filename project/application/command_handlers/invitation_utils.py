from typing import Optional

from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError, UnauthorizedError
from project.domain.models.entities.actor import Actor


def ensure_actor_is_invitation_receiver(
    actor: Actor, invitation_email: Optional[str], uow: AbstractUnitOfWork
):
    """Guard for the receiver-side half of a Revoke/Decline pair on the same
    row: `Actor` has no `email` field (only `user_id`/`app_installation_id`),
    so the receiver's identity must be resolved through `uow.users` and
    compared to the invitation's stored email, case-insensitively.
    """
    user = uow.users.get(actor.user_id) if actor.user_id is not None else None

    if user is None or user.email.lower() != (invitation_email or "").lower():
        raise UnauthorizedError("Actor is not the recipient of this invitation.")


def ensure_organization_invitation_exists(id: int, uow: AbstractUnitOfWork):
    organization_invitation = uow.organization_invitations.get(id)

    if not organization_invitation:  # pragma: no cover
        raise NotFoundError(f"Organization invitation with id {id} not found")

    return organization_invitation


def ensure_member_invitation_exists(id: int, uow: AbstractUnitOfWork):
    member_invitation = uow.member_invitations.get(id)

    if not member_invitation:  # pragma: no cover
        raise NotFoundError(f"Member invitation with id {id} not found")

    return member_invitation
