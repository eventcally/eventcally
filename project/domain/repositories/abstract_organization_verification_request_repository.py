import abc
from typing import Optional, Set

from project.domain.models.aggregates.organization_verification_request_aggregate import (
    OrganizationVerificationRequestAggregate,
)


class AbstractOrganizationVerificationRequestRepository(abc.ABC):
    def __init__(self):
        self.seen: Set[OrganizationVerificationRequestAggregate] = set()

    def add(self, verification_request: OrganizationVerificationRequestAggregate):
        self._add(verification_request)
        self.seen.add(verification_request)

    def update(self, verification_request: OrganizationVerificationRequestAggregate):
        self._update(verification_request)
        self.seen.add(verification_request)

    def get(self, object_id: int) -> Optional[OrganizationVerificationRequestAggregate]:
        verification_request = self._get(object_id)
        if verification_request:
            self.seen.add(verification_request)
        return verification_request

    def remove(self, verification_request: OrganizationVerificationRequestAggregate):
        self._remove(verification_request)
        self.seen.add(verification_request)

    @abc.abstractmethod
    def _add(
        self, verification_request: OrganizationVerificationRequestAggregate
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _update(
        self, verification_request: OrganizationVerificationRequestAggregate
    ):  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _get(
        self, object_id: int
    ) -> Optional[OrganizationVerificationRequestAggregate]:  # pragma: no cover
        raise NotImplementedError

    @abc.abstractmethod
    def _remove(
        self, verification_request: OrganizationVerificationRequestAggregate
    ):  # pragma: no cover
        raise NotImplementedError
