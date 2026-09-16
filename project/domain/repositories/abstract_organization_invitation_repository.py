import abc
from typing import Optional, Set

from project.domain.models.aggregates.admin_unit_invitation_aggregate import (
    AdminUnitInvitationAggregate,
)


class AbstractOrganizationInvitationRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[AdminUnitInvitationAggregate] = set()

    def add(self, organization_invitation: AdminUnitInvitationAggregate):
        self._add(organization_invitation)
        self.seen.add(organization_invitation)

    def update(self, organization_invitation: AdminUnitInvitationAggregate):
        self._update(organization_invitation)
        self.seen.add(organization_invitation)

    def get(self, object_id: int) -> Optional[AdminUnitInvitationAggregate]:
        organization_invitation = self._get(object_id)
        if organization_invitation:
            self.seen.add(organization_invitation)
        return organization_invitation

    def remove(self, organization_invitation: AdminUnitInvitationAggregate):
        self._remove(organization_invitation)
        self.seen.add(organization_invitation)

    @abc.abstractmethod
    def _add(
        self, organization_invitation: AdminUnitInvitationAggregate
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(
        self, organization_invitation: AdminUnitInvitationAggregate
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[AdminUnitInvitationAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(
        self, organization_invitation: AdminUnitInvitationAggregate
    ):  # pragma: no cover
        raise NotImplementedError
