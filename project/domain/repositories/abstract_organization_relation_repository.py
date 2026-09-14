import abc
from typing import Optional, Set

from project.domain.models.aggregates.organization_relation_aggregate import (
    OrganizationRelationAggregate,
)


class AbstractOrganizationRelationRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[OrganizationRelationAggregate] = set()

    def add(self, organization_relation: OrganizationRelationAggregate):
        self._add(organization_relation)
        self.seen.add(organization_relation)

    def update(self, organization_relation: OrganizationRelationAggregate):
        self._update(organization_relation)
        self.seen.add(organization_relation)

    def get(self, object_id: int) -> Optional[OrganizationRelationAggregate]:
        organization_relation = self._get(object_id)
        if organization_relation:
            self.seen.add(organization_relation)
        return organization_relation

    def get_by_source_and_target(
        self, source_admin_unit_id: int, target_admin_unit_id: int
    ) -> Optional[OrganizationRelationAggregate]:
        organization_relation = self._get_by_source_and_target(
            source_admin_unit_id, target_admin_unit_id
        )
        if organization_relation:
            self.seen.add(organization_relation)
        return organization_relation

    def remove(self, organization_relation: OrganizationRelationAggregate):
        self._remove(organization_relation)
        self.seen.add(organization_relation)

    @abc.abstractmethod
    def _add(
        self, organization_relation: OrganizationRelationAggregate
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(
        self, organization_relation: OrganizationRelationAggregate
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[OrganizationRelationAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get_by_source_and_target(
        self, source_admin_unit_id: int, target_admin_unit_id: int
    ) -> Optional[OrganizationRelationAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(
        self, organization_relation: OrganizationRelationAggregate
    ):  # pragma: no cover
        raise NotImplementedError
