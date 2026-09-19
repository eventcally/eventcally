from typing import Optional

from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.oauth2_client_aggregate import (
    OAuth2ClientAggregate,
)
from project.domain.models.entities.actor import Actor
from project.domain.types import ObjectId

from .authorization_utils import (
    ensure_actor_has_permission_for_admin_unit,
    ensure_actor_is_user,
)


def ensure_oauth2_client_exists(
    oauth2_client_id: int, uow: AbstractUnitOfWork
) -> OAuth2ClientAggregate:
    oauth2_client = uow.oauth2_clients.get(oauth2_client_id)

    if not oauth2_client:
        raise NotFoundError(f"OAuth2 client with id {oauth2_client_id} not found")

    return oauth2_client


def ensure_actor_can_manage_oauth2_client_owner(
    actor: Actor,
    user_id: Optional[ObjectId],
    admin_unit_id: Optional[ObjectId],
    uow: AbstractUnitOfWork,
):
    """Shared by create (owner ids come from the command) and update/delete
    (owner ids come from the loaded `OAuth2ClientAggregate`) — branches on
    which owner kind is set, exactly one of which is non-`None`."""
    if user_id is not None:
        ensure_actor_is_user(actor, user_id)
    else:
        ensure_actor_has_permission_for_admin_unit(
            actor, admin_unit_id, "oauth2_clients:write", uow
        )
