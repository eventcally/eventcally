from __future__ import annotations

import datetime
from typing import Optional

from project.domain.events.organization_deletion_cancelled import (
    OrganizationDeletionCancelled,
)
from project.domain.events.organization_deletion_requested import (
    OrganizationDeletionRequested,
)
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.types.object_id import ObjectId


class OrganizationAggregate(BaseAggregate):
    id: ObjectId
    deletion_requested_at: Optional[datetime.datetime] = None
    deletion_requested_by_id: Optional[ObjectId] = None

    def request_deletion(
        self,
        actor: Actor,
    ):
        self.deletion_requested_at = datetime.datetime.utcnow()
        self.deletion_requested_by_id = actor.user_id

        event = OrganizationDeletionRequested(
            actor=actor,
            id=self.id,
        )
        self.domain_events.append(event)

    def cancel_deletion(
        self,
        actor: Actor,
    ):
        self.deletion_requested_at = None
        self.deletion_requested_by_id = None

        event = OrganizationDeletionCancelled(
            actor=actor,
            id=self.id,
        )
        self.domain_events.append(event)
