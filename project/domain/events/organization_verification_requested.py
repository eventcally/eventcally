from project.domain.types import ObjectId

from .base import Event


class OrganizationVerificationRequested(Event):
    id: ObjectId
    source_admin_unit_id: ObjectId
    target_admin_unit_id: ObjectId
