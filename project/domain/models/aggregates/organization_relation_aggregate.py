from __future__ import annotations

from typing import Optional

from project.domain.errors import ConstraintError
from project.domain.events.organization_invitation_accepted import (
    OrganizationInvitationAccepted,
)
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import Unsetable


class OrganizationRelationAggregate(BaseAggregate):
    id: ObjectId
    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
    auto_verify_event_reference_requests: bool = False
    verify: bool = False
    invited: bool = False

    @classmethod
    def create(
        cls,
        actor: Actor,
        source_admin_unit_id: ObjectId,
        target_admin_unit_id: ObjectId,
        auto_verify_event_reference_requests: bool = False,
        verify: bool = False,
        invited: bool = False,
        accepted_invitation_email: Optional[str] = None,
        target_admin_unit_name: Optional[str] = None,
    ) -> OrganizationRelationAggregate:
        if source_admin_unit_id == target_admin_unit_id:
            raise ConstraintError("There must be no self-reference.")

        instance = cls(
            id=-1,
            source_admin_unit_id=source_admin_unit_id,
            target_admin_unit_id=target_admin_unit_id,
            auto_verify_event_reference_requests=auto_verify_event_reference_requests,
            verify=verify,
            invited=invited,
        )

        if accepted_invitation_email and target_admin_unit_name:
            event = OrganizationInvitationAccepted(
                actor=actor,
                id=-1,
                inviting_admin_unit_id=source_admin_unit_id,
                new_admin_unit_id=target_admin_unit_id,
                new_admin_unit_name=target_admin_unit_name,
                accepting_user_email=accepted_invitation_email,
            )
            instance.domain_events.append(event)

        return instance

    def update(
        self,
        actor: Actor,
        auto_verify_event_reference_requests: Unsetable[bool] = unset,
        verify: Unsetable[bool] = unset,
    ):
        self._update_field_with_value(
            "auto_verify_event_reference_requests",
            auto_verify_event_reference_requests,
        )
        self._update_field_with_value("verify", verify)

        self.validate_self()

    def delete(self, actor: Actor):
        pass
