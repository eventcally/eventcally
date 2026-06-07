import abc
from typing import Set

from project.domain.models.aggregates.organization_member_aggregate import (
    OrganisationMemberAggregate,
)
from project.domain.types.object_id import ObjectId


class AbstractOrganizationMemberRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[OrganisationMemberAggregate] = set()

    def get_all_with_permission(
        self, admin_unit_id: ObjectId, permission: str
    ) -> list[OrganisationMemberAggregate]:
        return self._get_all_with_permission(admin_unit_id, permission)

    @abc.abstractmethod
    def _get_all_with_permission(
        self, admin_unit_id: ObjectId, permission: str
    ) -> list[OrganisationMemberAggregate]:  # pragma: no cover
        raise NotImplementedError
