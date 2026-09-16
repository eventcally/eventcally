import abc
from typing import Optional, Set

from project.domain.models.aggregates.admin_unit_member_invitation_aggregate import (
    AdminUnitMemberInvitationAggregate,
)


class AbstractMemberInvitationRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[AdminUnitMemberInvitationAggregate] = set()

    def add(self, member_invitation: AdminUnitMemberInvitationAggregate):
        self._add(member_invitation)
        self.seen.add(member_invitation)

    def update(self, member_invitation: AdminUnitMemberInvitationAggregate):
        self._update(member_invitation)
        self.seen.add(member_invitation)

    def get(self, object_id: int) -> Optional[AdminUnitMemberInvitationAggregate]:
        member_invitation = self._get(object_id)
        if member_invitation:
            self.seen.add(member_invitation)
        return member_invitation

    def remove(self, member_invitation: AdminUnitMemberInvitationAggregate):
        self._remove(member_invitation)
        self.seen.add(member_invitation)

    @abc.abstractmethod
    def _add(
        self, member_invitation: AdminUnitMemberInvitationAggregate
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(
        self, member_invitation: AdminUnitMemberInvitationAggregate
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[AdminUnitMemberInvitationAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(
        self, member_invitation: AdminUnitMemberInvitationAggregate
    ):  # pragma: no cover
        raise NotImplementedError
