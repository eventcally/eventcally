from __future__ import annotations

from typing import Optional

from project.domain import events
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types import unset
from project.domain.types.object_id import ObjectId
from project.domain.types.unsetable import NullableUnsetable, Unsetable


class AdminUnitInvitationAggregate(BaseAggregate):
    id: ObjectId
    admin_unit_id: ObjectId
    email: str
    admin_unit_name: Optional[str] = None
    relation_auto_verify_event_reference_requests: bool = False
    relation_verify: bool = False

    @classmethod
    def create(
        cls,
        actor: Actor,
        admin_unit_id: ObjectId,
        email: str,
        admin_unit_name: Optional[str] = None,
        relation_auto_verify_event_reference_requests: bool = False,
        relation_verify: bool = False,
    ) -> AdminUnitInvitationAggregate:
        instance = cls(
            id=-1,
            admin_unit_id=admin_unit_id,
            email=email,
            admin_unit_name=admin_unit_name,
            relation_auto_verify_event_reference_requests=(
                relation_auto_verify_event_reference_requests
            ),
            relation_verify=relation_verify,
        )

        event = events.OrganizationInvitationCreated(
            actor=actor,
            id=-1,
            admin_unit_id=admin_unit_id,
            email=email,
        )
        instance.domain_events.append(event)

        return instance

    def update(
        self,
        actor: Actor,
        admin_unit_name: NullableUnsetable[str] = unset,
        relation_auto_verify_event_reference_requests: Unsetable[bool] = unset,
        relation_verify: Unsetable[bool] = unset,
    ):
        self._update_field_with_value("admin_unit_name", admin_unit_name)
        self._update_field_with_value(
            "relation_auto_verify_event_reference_requests",
            relation_auto_verify_event_reference_requests,
        )
        self._update_field_with_value("relation_verify", relation_verify)

        self.validate_self()

    def delete(self, actor: Actor):
        pass
