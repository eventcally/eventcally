from typing import Dict, Optional, TypeVar

from project.application.read_models.event_visibility_read_model import (
    EventVisibilityReadModel,
)
from project.application.services.actor_authorization_service import (
    ActorAuthorizationService,
)
from project.domain.errors import UnauthorizedError
from project.domain.models.entities.actor import Actor
from project.domain.models.enums.event_public_status import EventPublicStatus

READ_PRIVATE_EVENTS_PERMISSION = "events:read"

EventT = TypeVar("EventT")


class EventVisibilityService:
    """The one rule for who may read an event (`access.can_read_event`): published
    events of verified organizations are public, planned ones need the right to plan,
    everything else needs `events:read` for the organization."""

    def __init__(self, authz: ActorAuthorizationService):
        self.authz = authz

    def can_read_private_events(
        self, actor: Optional[Actor], admin_unit_id: int
    ) -> bool:
        return self.authz.has_permission_for_admin_unit(
            actor, admin_unit_id, READ_PRIVATE_EVENTS_PERMISSION
        )

    def can_read(
        self, actor: Optional[Actor], visibility: EventVisibilityReadModel
    ) -> bool:
        if (
            visibility.public_status == EventPublicStatus.published
            and visibility.admin_unit_is_verified
        ):
            return True

        if (
            visibility.public_status == EventPublicStatus.planned
            and visibility.admin_unit_is_verified
            and self.authz.can_use_planning(actor)
        ):
            return True

        return self.can_read_private_events(actor, visibility.admin_unit_id)

    def ensure_can_read(
        self, actor: Optional[Actor], visibility: EventVisibilityReadModel
    ):
        if not self.can_read(actor, visibility):
            raise UnauthorizedError(
                f"Actor is not permitted to read event {visibility.event_id}."
            )

    def redact_internal_tags(self, actor: Optional[Actor], events: list) -> list:
        """Events whose organization the actor may not read privately lose their
        `internal_tags` (one permission check per organization)."""
        allowed: Dict[int, bool] = {}
        result = []

        for event in events:
            if event.internal_tags is None:
                result.append(event)
                continue

            if event.admin_unit_id not in allowed:
                allowed[event.admin_unit_id] = self.can_read_private_events(
                    actor, event.admin_unit_id
                )

            if allowed[event.admin_unit_id]:
                result.append(event)
            else:
                result.append(event.model_copy(update={"internal_tags": None}))

        return result

    def redact_detail(self, actor: Optional[Actor], detail):
        """`redact_internal_tags` plus what only the organization's members see: who
        created and last changed the event, and its reference requests."""
        (detail,) = self.redact_internal_tags(actor, [detail])
        updates = {}

        if not self.can_read_private_events(actor, detail.admin_unit_id):
            updates.update(created_by_label=None, updated_by_label=None)

        if detail.reference_requests and not self.authz.has_permission_for_admin_unit(
            actor, detail.admin_unit_id, "outgoing_event_reference_requests:write"
        ):
            updates["reference_requests"] = []

        return detail.model_copy(update=updates) if updates else detail
