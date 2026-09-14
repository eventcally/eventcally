from __future__ import annotations

from project.domain.errors import ConstraintError
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
