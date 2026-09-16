from typing import Optional

from project.domain.abstract_unit_of_work import AbstractUnitOfWork
from project.domain.errors import NotFoundError
from project.domain.models.aggregates.api_key_aggregate import ApiKeyAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import ObjectId

from .authorization_utils import (
    ensure_actor_has_permission_for_admin_unit,
    ensure_actor_is_user,
)


def ensure_api_key_exists(api_key_id: int, uow: AbstractUnitOfWork) -> ApiKeyAggregate:
    api_key = uow.api_keys.get(api_key_id)

    if not api_key:
        raise NotFoundError(f"Api key with id {api_key_id} not found")

    return api_key


def ensure_actor_can_manage_api_key_owner(
    actor: Actor,
    user_id: Optional[ObjectId],
    admin_unit_id: Optional[ObjectId],
    uow: AbstractUnitOfWork,
):
    """Shared by create (owner ids come from the command) and update/delete
    (owner ids come from the loaded `ApiKeyAggregate`) — branches on which
    owner kind is set, exactly one of which is non-`None`."""
    if user_id is not None:
        ensure_actor_is_user(actor, user_id)
    else:
        ensure_actor_has_permission_for_admin_unit(
            actor, admin_unit_id, "api_keys:write", uow
        )
