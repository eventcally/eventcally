import abc
from typing import Optional, Set

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

    def get_by_admin_unit_and_user(
        self, admin_unit_id: ObjectId, user_id: ObjectId
    ) -> Optional[OrganisationMemberAggregate]:
        member = self._get_by_admin_unit_and_user(admin_unit_id, user_id)
        if member:
            self.seen.add(member)
        return member

    def get(self, object_id: ObjectId) -> Optional[OrganisationMemberAggregate]:
        member = self._get(object_id)
        if member:
            self.seen.add(member)
        return member

    def add(self, member: OrganisationMemberAggregate):
        self._add(member)
        self.seen.add(member)

    def update(self, member: OrganisationMemberAggregate):
        self._update(member)
        self.seen.add(member)

    def remove(self, member: OrganisationMemberAggregate):
        self._remove(member)
        self.seen.add(member)

    @abc.abstractmethod
    def _get_all_with_permission(
        self, admin_unit_id: ObjectId, permission: str
    ) -> list[OrganisationMemberAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_by_admin_unit_and_user(
        self, admin_unit_id: ObjectId, user_id: ObjectId
    ) -> Optional[OrganisationMemberAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: ObjectId
    ) -> Optional[OrganisationMemberAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _add(self, member: OrganisationMemberAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, member: OrganisationMemberAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, member: OrganisationMemberAggregate):  # pragma: no cover
        raise NotImplementedError
