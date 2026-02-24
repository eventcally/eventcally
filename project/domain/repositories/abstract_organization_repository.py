import abc
from typing import Set

from project.domain.types.object_id import ObjectId
from project.models import AdminUnit
from project.models.admin_unit import AdminUnitMember


class AbstractOrganizationRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[AdminUnit] = set()

    def add(self, organization: AdminUnit):  # pragma: no cover
        self._add(organization)
        self.seen.add(organization)

    def get(self, object_id: int) -> AdminUnit:
        organization = self._get(object_id)
        if organization:
            self.seen.add(organization)
        return organization

    def get_members_with_permission(
        self, organization_id: ObjectId, permission: str
    ) -> list[AdminUnitMember]:
        return self._get_members_with_permission(organization_id, permission)

    def remove(self, organization: AdminUnit):  # pragma: no cover
        self._remove(organization)
        self.seen.add(organization)

    @abc.abstractmethod
    def _add(self, organization: AdminUnit):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> AdminUnit:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, organization: AdminUnit):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_members_with_permission(
        self, organization_id: ObjectId, permission: str
    ) -> list[AdminUnitMember]:  # pragma: no cover
        raise NotImplementedError
