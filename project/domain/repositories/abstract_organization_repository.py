import abc
from typing import Set

from project.domain.models.aggregates.organization_aggregate import (
    OrganizationAggregate,
)


class AbstractOrganizationRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[OrganizationAggregate] = set()

    def update(self, organization: OrganizationAggregate):
        self._update(organization)
        self.seen.add(organization)

    def get(self, object_id: int) -> OrganizationAggregate:
        organization = self._get(object_id)
        if organization:
            self.seen.add(organization)
        return organization

    @abc.abstractmethod
    def _get(self, object_id: int) -> OrganizationAggregate:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(self, organization: OrganizationAggregate):  # pragma: no cover
        raise NotImplementedError
