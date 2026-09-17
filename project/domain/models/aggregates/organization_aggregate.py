from __future__ import annotations

import datetime
from typing import List, Optional

from project.domain.events.organization_deletion_cancelled import (
    OrganizationDeletionCancelled,
)
from project.domain.events.organization_deletion_requested import (
    OrganizationDeletionRequested,
)
from project.domain.models.aggregates.base_aggregate import BaseAggregate
from project.domain.models.entities.actor import Actor
from project.domain.models.entities.image_entity import ImageEntity
from project.domain.models.value_objects.location_value_object import (
    LocationValueObject,
)
from project.domain.types.object_id import ObjectId


class OrganizationAggregate(BaseAggregate):
    id: ObjectId
    name: Optional[str] = None
    short_name: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    fax: Optional[str] = None
    logo: Optional[ImageEntity] = None
    deletion_requested_at: Optional[datetime.datetime] = None
    deletion_requested_by_id: Optional[ObjectId] = None
    can_verify_other: bool = False
    incoming_verification_requests_allowed: bool = False
    incoming_verification_requests_postal_codes: List[str] = []
    incoming_reference_requests_allowed: bool = False
    location: Optional[LocationValueObject] = None
    max_api_keys: int = 1

    @classmethod
    def create(
        cls,
        actor: Actor,
        name: str,
        short_name: str,
        description: Optional[str] = None,
        url: Optional[str] = None,
        email: Optional[str] = None,
        phone: Optional[str] = None,
        fax: Optional[str] = None,
        location: Optional[LocationValueObject] = None,
        logo: Optional[ImageEntity] = None,
    ) -> OrganizationAggregate:
        return cls(
            id=-1,
            name=name,
            short_name=short_name,
            description=description,
            url=url,
            email=email,
            phone=phone,
            fax=fax,
            location=location,
            logo=logo,
        )

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
