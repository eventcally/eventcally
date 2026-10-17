from enum import Enum
from typing import Optional

from project.application.queries.base import Query
from project.domain.types.object_id import ObjectId


class ResourceKind(str, Enum):
    """Resources whose owning organization API decorators look up."""

    event = "event"
    event_place = "event_place"
    event_organizer = "event_organizer"
    custom_widget = "custom_widget"
    event_reference = "event_reference"
    event_reference_request = "event_reference_request"
    event_reference_request_target = "event_reference_request_target"
    organization_relation = "organization_relation"
    organization_invitation = "organization_invitation"
    verification_request_source = "verification_request_source"
    verification_request_target = "verification_request_target"


class GetResourceOwnerQuery(Query[Optional[ObjectId]]):
    """The id of the organization a resource belongs to (the requesting side for
    relations and verification requests, the event owner for reference requests),
    or `None` if the resource does not exist."""

    kind: ResourceKind
    id: ObjectId
