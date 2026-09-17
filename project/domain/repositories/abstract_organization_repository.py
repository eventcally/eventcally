import abc
from typing import Set

from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)


class AbstractOrganizationRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[OrganizationAggregate] = set()

    def add(self, organization: OrganizationAggregate):
        self._add(organization)
        self.seen.add(organization)

    def update(self, organization: OrganizationAggregate):
        self._update(organization)
        self.seen.add(organization)

    def get(self, object_id: int) -> OrganizationAggregate:
        organization = self._get(object_id)
        if organization:
            self.seen.add(organization)
        return organization

    def remove(self, organization: OrganizationAggregate):
        self._remove(organization)
        self.seen.add(organization)

    @abc.abstractmethod
    def _add(self, organization: OrganizationAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(self, object_id: int) -> OrganizationAggregate:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, organization: OrganizationAggregate):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(self, organization: OrganizationAggregate):  # pragma: no cover
        raise NotImplementedError
